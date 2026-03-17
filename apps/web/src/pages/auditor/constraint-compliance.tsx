// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M12-05: Constraint Compliance Assessment
 *
 * Auditor view for assessing constraint compliance across a session:
 * - 5-dimension compliance summary
 * - Held action audit trail (approved/denied)
 * - Assessment template for structured evaluation
 */

import { useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle,
  ClipboardCheck,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { VerificationBundle } from "@/types/api";
import type { ChainVerificationResult as VerResult } from "@/lib/chain-verifier";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Compliance dimension
// ---------------------------------------------------------------------------

const DIMENSIONS = [
  "financial",
  "operational",
  "temporal",
  "data_access",
  "communication",
] as const;

const dimensionLabels: Record<string, string> = {
  financial: "Spending",
  operational: "Operations",
  temporal: "Time",
  data_access: "Data Access",
  communication: "Communication",
};

interface AssessmentItem {
  dimension: string;
  question: string;
  answer: "compliant" | "non_compliant" | "not_assessed";
  notes: string;
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function ConstraintCompliancePage() {
  const location = useLocation();
  const navigate = useNavigate();

  const state = location.state as {
    bundle?: VerificationBundle;
    result?: VerResult;
  } | null;
  const bundle = state?.bundle;
  const result = state?.result;

  const [assessments, setAssessments] = useState<AssessmentItem[]>(
    DIMENSIONS.map((dim) => ({
      dimension: dim,
      question: `Were ${dimensionLabels[dim]?.toLowerCase() ?? dim} constraints adhered to throughout the session?`,
      answer: "not_assessed",
      notes: "",
    })),
  );

  if (!bundle) {
    return (
      <div className="mx-auto max-w-3xl space-y-6 p-4 md:p-8">
        <p className="text-sm text-[var(--muted-foreground)]">
          No bundle data available.{" "}
          <Link
            to="/verify"
            className="font-medium text-[var(--primary)] hover:underline"
          >
            Upload a bundle first.
          </Link>
        </p>
      </div>
    );
  }

  // Extract held actions from bundle entries
  const heldActions = bundle.entries.filter((entry) => {
    const payload = entry.payload;
    return (
      (payload.type as string) === "held_action" ||
      (payload.record_type as string) === "held_action"
    );
  });

  function updateAssessment(
    index: number,
    field: "answer" | "notes",
    value: string,
  ) {
    setAssessments((prev) =>
      prev.map((a, i) => (i === index ? { ...a, [field]: value } : a)),
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-4 md:p-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Compliance Assessment
          </h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            Session: {bundle.session_id.slice(0, 12)}...
          </p>
        </div>
      </div>

      {/* Chain verification summary */}
      {result && (
        <Card>
          <CardContent className="pt-0">
            <div className="flex items-center gap-3">
              {result.valid ? (
                <CheckCircle className="h-5 w-5 text-[var(--trust-valid)]" />
              ) : (
                <XCircle className="h-5 w-5 text-[var(--trust-invalid)]" />
              )}
              <div>
                <p className="text-sm font-medium">
                  {result.valid
                    ? "Trust chain verified"
                    : `Chain has ${result.breaks.length} break${result.breaks.length !== 1 ? "s" : ""}`}
                </p>
                <p className="text-xs text-[var(--muted-foreground)]">
                  {result.verifiedEntries} of {result.totalEntries} entries
                  verified
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Held action audit trail */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Held Action Audit Trail
          </CardTitle>
        </CardHeader>
        <CardContent>
          {heldActions.length === 0 ? (
            <p className="py-4 text-center text-sm text-[var(--muted-foreground)]">
              No held actions were recorded in this session.
            </p>
          ) : (
            <div className="space-y-3">
              {heldActions.map((entry, i) => {
                const payload = entry.payload;
                return (
                  <div
                    key={i}
                    className="rounded-md border border-[var(--border)] p-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">
                        {(payload.action as string) ?? "Unknown action"}
                      </span>
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-xs font-medium",
                          (payload.resolution as string) === "approved"
                            ? "trust-auto-bg"
                            : (payload.resolution as string) === "denied"
                              ? "trust-blocked-bg"
                              : "trust-held-bg",
                        )}
                      >
                        {(payload.resolution as string) ?? "pending"}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-[var(--muted-foreground)]">
                      Dimension: {(payload.dimension as string) ?? "unknown"} |
                      Reason: {(payload.reason as string) ?? "not specified"}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Assessment template */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ClipboardCheck className="h-4 w-4" />
            Structured Assessment
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {assessments.map((assessment, i) => (
            <div
              key={assessment.dimension}
              className="space-y-2 rounded-md border border-[var(--border)] p-3"
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">
                  {dimensionLabels[assessment.dimension] ??
                    assessment.dimension}
                </p>
                <div className="flex gap-1">
                  {(
                    ["compliant", "non_compliant", "not_assessed"] as const
                  ).map((answer) => (
                    <button
                      key={answer}
                      type="button"
                      onClick={() => updateAssessment(i, "answer", answer)}
                      className={cn(
                        "rounded-md px-2 py-1 text-xs font-medium transition-colors",
                        assessment.answer === answer
                          ? answer === "compliant"
                            ? "bg-[var(--trust-auto)] text-white"
                            : answer === "non_compliant"
                              ? "bg-[var(--trust-blocked)] text-white"
                              : "bg-[var(--muted)] text-[var(--foreground)]"
                          : "bg-[var(--muted)] text-[var(--muted-foreground)] hover:bg-[var(--accent)]",
                      )}
                    >
                      {answer === "compliant"
                        ? "Compliant"
                        : answer === "non_compliant"
                          ? "Non-compliant"
                          : "Not assessed"}
                    </button>
                  ))}
                </div>
              </div>
              <p className="text-xs text-[var(--muted-foreground)]">
                {assessment.question}
              </p>
              <textarea
                value={assessment.notes}
                onChange={(e) => updateAssessment(i, "notes", e.target.value)}
                placeholder="Auditor notes..."
                rows={2}
                className="w-full rounded-md border border-[var(--input)] bg-transparent px-3 py-2 text-xs shadow-xs outline-none placeholder:text-[var(--muted-foreground)] focus-visible:border-[var(--ring)]"
              />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
