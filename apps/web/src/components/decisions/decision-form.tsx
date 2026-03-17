// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M11-05: Decision Recording Form
 *
 * Quick-entry form for recording decisions during a CO session.
 * Optimized for a 30-second completion target. Fields:
 * - What (required): the decision made
 * - Why (required): reasoning behind the decision
 * - Alternatives (optional): other options considered
 * - Confidence (optional): slider from 0 to 100%
 */

import { useState } from "react";
import { Loader2, Plus, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useDecide } from "@/services/hooks";

interface DecisionFormProps {
  sessionId: string;
  onSuccess?: () => void;
}

export function DecisionForm({ sessionId, onSuccess }: DecisionFormProps) {
  const [decision, setDecision] = useState("");
  const [rationale, setRationale] = useState("");
  const [alternatives, setAlternatives] = useState<string[]>([]);
  const [newAlt, setNewAlt] = useState("");
  const [confidence, setConfidence] = useState(80);

  const decideMutation = useDecide();

  function addAlternative() {
    const trimmed = newAlt.trim();
    if (trimmed && !alternatives.includes(trimmed)) {
      setAlternatives([...alternatives, trimmed]);
      setNewAlt("");
    }
  }

  function removeAlternative(index: number) {
    setAlternatives(alternatives.filter((_, i) => i !== index));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!decision.trim() || !rationale.trim()) return;

    await decideMutation.mutateAsync({
      sessionId,
      data: {
        decision: decision.trim(),
        rationale: rationale.trim(),
        alternatives: alternatives.length > 0 ? alternatives : undefined,
        confidence: confidence / 100,
      },
    });

    // Reset form
    setDecision("");
    setRationale("");
    setAlternatives([]);
    setNewAlt("");
    setConfidence(80);
    onSuccess?.();
  }

  const canSubmit =
    decision.trim().length > 0 &&
    rationale.trim().length > 0 &&
    !decideMutation.isPending;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* What */}
      <div className="space-y-1.5">
        <Label htmlFor="decision">What did you decide?</Label>
        <Input
          id="decision"
          placeholder="Describe the decision you made..."
          value={decision}
          onChange={(e) => setDecision(e.target.value)}
          autoFocus
        />
      </div>

      {/* Why */}
      <div className="space-y-1.5">
        <Label htmlFor="rationale">Why?</Label>
        <textarea
          id="rationale"
          placeholder="What reasoning led to this decision?"
          value={rationale}
          onChange={(e) => setRationale(e.target.value)}
          rows={2}
          className="w-full rounded-md border border-[var(--input)] bg-transparent px-3 py-2 text-sm shadow-xs outline-none placeholder:text-[var(--muted-foreground)] focus-visible:border-[var(--ring)] focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]/50"
        />
      </div>

      {/* Alternatives */}
      <div className="space-y-1.5">
        <Label>Alternatives considered (optional)</Label>
        {alternatives.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {alternatives.map((alt, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 rounded-full bg-[var(--muted)] px-2.5 py-1 text-xs"
              >
                {alt}
                <button
                  type="button"
                  onClick={() => removeAlternative(i)}
                  className="text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        )}
        <div className="flex gap-2">
          <Input
            placeholder="Add an alternative..."
            value={newAlt}
            onChange={(e) => setNewAlt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addAlternative();
              }
            }}
          />
          <Button
            type="button"
            variant="outline"
            size="icon"
            onClick={addAlternative}
            disabled={!newAlt.trim()}
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Confidence */}
      <div className="space-y-1.5">
        <Label htmlFor="confidence">Confidence: {confidence}%</Label>
        <input
          id="confidence"
          type="range"
          min={0}
          max={100}
          step={5}
          value={confidence}
          onChange={(e) => setConfidence(Number(e.target.value))}
          className="w-full accent-[var(--primary)]"
        />
        <div className="flex justify-between text-xs text-[var(--muted-foreground)]">
          <span>Low</span>
          <span>High</span>
        </div>
      </div>

      {/* Error */}
      {decideMutation.error && (
        <p className="text-sm text-[var(--trust-blocked)]">
          Something went wrong recording this decision. Please try again.
        </p>
      )}

      {/* Submit */}
      <Button type="submit" disabled={!canSubmit} className="w-full">
        {decideMutation.isPending ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Recording...
          </>
        ) : (
          "Record Decision"
        )}
      </Button>
    </form>
  );
}
