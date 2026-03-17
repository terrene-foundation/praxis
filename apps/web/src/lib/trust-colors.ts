// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Trust state color and label utilities.
 *
 * Maps gradient levels to CSS classes and human-readable labels.
 * Uses the CSS custom properties defined in index.css.
 */

import type { GradientLevel } from "@/types/api";

export function trustColorClass(level: GradientLevel): string {
  switch (level) {
    case "auto_approved":
      return "trust-auto";
    case "flagged":
      return "trust-flagged";
    case "held":
      return "trust-held";
    case "blocked":
      return "trust-blocked";
  }
}

export function trustBgClass(level: GradientLevel): string {
  switch (level) {
    case "auto_approved":
      return "trust-auto-bg";
    case "flagged":
      return "trust-flagged-bg";
    case "held":
      return "trust-held-bg";
    case "blocked":
      return "trust-blocked-bg";
  }
}

export function trustLabel(level: GradientLevel): string {
  switch (level) {
    case "auto_approved":
      return "Approved";
    case "flagged":
      return "Flagged";
    case "held":
      return "Held";
    case "blocked":
      return "Blocked";
  }
}

export function trustCssVar(level: GradientLevel): string {
  switch (level) {
    case "auto_approved":
      return "var(--trust-auto)";
    case "flagged":
      return "var(--trust-flagged)";
    case "held":
      return "var(--trust-held)";
    case "blocked":
      return "var(--trust-blocked)";
  }
}
