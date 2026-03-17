# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Constraint calibration analysis — detecting misconfigured constraints.

Analyzes constraint enforcement data to identify:
- Under-utilized dimensions (constraints set too loose)
- Boundary pressure (too many evaluations near the threshold)
- False positives (HELD actions that are always approved)
- False negatives (actions that should have been held but weren't)

This module provides signals to help practitioners right-size their
constraint envelopes so the verification gradient works effectively.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class CalibrationAnalyzer:
    """Analyzes constraint calibration across sessions for a domain.

    Reads ConstraintEvent and HeldAction records from the database and
    produces a calibration report with actionable recommendations.
    """

    def analyze(self, domain: str) -> dict[str, Any]:
        """Run calibration analysis for a domain.

        Args:
            domain: CO domain to analyze (e.g. "coc", "coe").

        Returns:
            Dict with keys:
                - domain: str
                - total_evaluations: int
                - dimensions: per-dimension calibration data
                - boundary_pressure: per-dimension % of evaluations near threshold
                - false_positive_rate: fraction of HELD actions always approved
                - false_negative_estimate: dict with indicators
                - recommendations: list of actionable suggestions
        """
        from praxis.persistence.db_ops import db_list

        # Get all sessions for this domain
        sessions = db_list("Session", filter={"domain": domain}, limit=10000)
        session_ids = {s["id"] for s in sessions}

        if not session_ids:
            return self._empty_result(domain)

        # Get all constraint events across those sessions
        all_events: list[dict] = []
        for sid in session_ids:
            events = db_list(
                "ConstraintEvent",
                filter={"session_id": sid},
                limit=10000,
            )
            all_events.extend(events)

        # Get all held actions across those sessions
        all_held: list[dict] = []
        for sid in session_ids:
            held = db_list(
                "HeldAction",
                filter={"session_id": sid},
                limit=10000,
            )
            all_held.extend(held)

        total_evaluations = len(all_events)

        if total_evaluations == 0:
            return self._empty_result(domain)

        # Per-dimension analysis
        dimensions_data = self._analyze_dimensions(all_events)

        # Boundary pressure: % of evaluations with utilization > 80%
        boundary_pressure = self._compute_boundary_pressure(all_events)

        # False positive rate: HELD actions that were always approved
        false_positive_rate = self._compute_false_positive_rate(all_held)

        # False negative estimate: auto_approved actions in dimensions near limits
        false_negative_estimate = self._estimate_false_negatives(all_events)

        # Build recommendations
        recommendations = self._build_recommendations(
            dimensions_data,
            boundary_pressure,
            false_positive_rate,
            false_negative_estimate,
        )

        return {
            "domain": domain,
            "total_evaluations": total_evaluations,
            "total_sessions": len(session_ids),
            "dimensions": dimensions_data,
            "boundary_pressure": boundary_pressure,
            "false_positive_rate": round(false_positive_rate, 4),
            "false_negative_estimate": false_negative_estimate,
            "recommendations": recommendations,
        }

    def _analyze_dimensions(self, events: list[dict]) -> dict[str, dict]:
        """Analyze utilization distribution per constraint dimension."""
        from praxis.core.constraint import CONSTRAINT_DIMENSIONS

        result: dict[str, dict] = {}

        for dim in CONSTRAINT_DIMENSIONS:
            dim_events = [e for e in events if e.get("dimension") == dim]

            if not dim_events:
                result[dim] = {
                    "total_evaluations": 0,
                    "avg_utilization": 0.0,
                    "max_utilization": 0.0,
                    "min_utilization": 0.0,
                    "auto_approved": 0,
                    "flagged": 0,
                    "held": 0,
                    "blocked": 0,
                }
                continue

            utilizations = [float(e.get("utilization", 0.0)) for e in dim_events]
            gradient_counts = {
                "auto_approved": 0,
                "flagged": 0,
                "held": 0,
                "blocked": 0,
            }
            for e in dim_events:
                gr = e.get("gradient_result", "auto_approved")
                if gr in gradient_counts:
                    gradient_counts[gr] += 1

            result[dim] = {
                "total_evaluations": len(dim_events),
                "avg_utilization": round(sum(utilizations) / len(utilizations), 4),
                "max_utilization": round(max(utilizations), 4),
                "min_utilization": round(min(utilizations), 4),
                "auto_approved": gradient_counts["auto_approved"],
                "flagged": gradient_counts["flagged"],
                "held": gradient_counts["held"],
                "blocked": gradient_counts["blocked"],
            }

        return result

    def _compute_boundary_pressure(self, events: list[dict]) -> dict[str, float]:
        """Compute boundary pressure per dimension.

        Boundary pressure = fraction of evaluations with utilization > 0.80.
        High boundary pressure means the constraint is set too tight or the
        practitioner is consistently operating near the limit.
        """
        from praxis.core.constraint import CONSTRAINT_DIMENSIONS

        pressure: dict[str, float] = {}

        for dim in CONSTRAINT_DIMENSIONS:
            dim_events = [e for e in events if e.get("dimension") == dim]
            if not dim_events:
                pressure[dim] = 0.0
                continue

            high_util = sum(1 for e in dim_events if float(e.get("utilization", 0.0)) > 0.80)
            pressure[dim] = round(high_util / len(dim_events), 4)

        return pressure

    def _compute_false_positive_rate(self, held_actions: list[dict]) -> float:
        """Compute the false positive rate for held actions.

        False positive = a held action that was approved (suggesting it
        didn't actually need to be held). This is the fraction of resolved
        held actions that were approved.
        """
        resolved = [h for h in held_actions if h.get("resolved")]
        if not resolved:
            return 0.0

        approved = sum(1 for h in resolved if h.get("resolution") == "approved")
        return approved / len(resolved)

    def _estimate_false_negatives(self, events: list[dict]) -> dict[str, Any]:
        """Estimate false negative rate.

        False negatives are harder to detect directly. We estimate by looking
        at auto_approved events with utilization in the 60-69% range (just
        below the flagging threshold). A high concentration here suggests
        the thresholds might be too high.
        """
        near_threshold = [
            e
            for e in events
            if e.get("gradient_result") == "auto_approved"
            and 0.60 <= float(e.get("utilization", 0.0)) < 0.70
        ]

        total_auto_approved = sum(1 for e in events if e.get("gradient_result") == "auto_approved")

        near_threshold_rate = (
            len(near_threshold) / total_auto_approved if total_auto_approved > 0 else 0.0
        )

        return {
            "near_threshold_count": len(near_threshold),
            "total_auto_approved": total_auto_approved,
            "near_threshold_rate": round(near_threshold_rate, 4),
            "concern": near_threshold_rate > 0.20,
        }

    def _build_recommendations(
        self,
        dimensions: dict[str, dict],
        boundary_pressure: dict[str, float],
        false_positive_rate: float,
        false_negative_estimate: dict,
    ) -> list[str]:
        """Build actionable calibration recommendations."""
        recs: list[str] = []

        # High false positive rate
        if false_positive_rate > 0.80:
            recs.append(
                f"False positive rate is {false_positive_rate:.0%} "
                f"(most held actions are approved). Consider relaxing "
                f"constraints in dimensions that frequently trigger holds, "
                f"or raising the hold threshold."
            )

        # Per-dimension pressure
        for dim, pressure in boundary_pressure.items():
            if pressure > 0.30:
                recs.append(
                    f"High boundary pressure on '{dim}' dimension "
                    f"({pressure:.0%} of evaluations >80% utilization). "
                    f"Consider increasing the limit or reviewing the constraint."
                )

        # Under-utilized dimensions
        for dim, data in dimensions.items():
            if data["total_evaluations"] > 10 and data["avg_utilization"] < 0.10:
                recs.append(
                    f"Dimension '{dim}' has very low average utilization "
                    f"({data['avg_utilization']:.0%}). The constraint may "
                    f"be set too loosely to provide meaningful enforcement."
                )

        # False negative concerns
        if false_negative_estimate.get("concern"):
            recs.append(
                f"{false_negative_estimate['near_threshold_count']} "
                f"auto-approved evaluations were near the flagging threshold "
                f"(60-69% utilization). The auto-approve threshold may be "
                f"too high for this workload."
            )

        if not recs:
            recs.append(
                "Constraint calibration appears healthy. " "No significant issues detected."
            )

        return recs

    def _empty_result(self, domain: str) -> dict[str, Any]:
        """Return an empty calibration result."""
        return {
            "domain": domain,
            "total_evaluations": 0,
            "total_sessions": 0,
            "dimensions": {},
            "boundary_pressure": {},
            "false_positive_rate": 0.0,
            "false_negative_estimate": {
                "near_threshold_count": 0,
                "total_auto_approved": 0,
                "near_threshold_rate": 0.0,
                "concern": False,
            },
            "recommendations": [
                "No constraint evaluation data available. "
                "Run some sessions to accumulate calibration data."
            ],
        }
