// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M11-02: Session Wizard
 *
 * Multi-step guided flow for creating a new CO session:
 * 1. Name & Description
 * 2. Domain selection (6 domains)
 * 3. Constraint template (strict / moderate / permissive)
 * 4. Review & Create
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Check,
  Code,
  Gavel,
  Globe,
  Loader2,
  Scale,
  Shield,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateSession } from "@/services/hooks";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Domain definitions
// ---------------------------------------------------------------------------

interface DomainOption {
  id: string;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const DOMAINS: DomainOption[] = [
  {
    id: "coc",
    label: "Software Development",
    description:
      "CO for code generation, architecture decisions, and development workflows.",
    icon: Code,
  },
  {
    id: "coe",
    label: "Education",
    description:
      "CO for learning, process-based assessment, and deliberation logs.",
    icon: BookOpen,
  },
  {
    id: "cog",
    label: "Governance",
    description:
      "CO for organizational governance and constitutional compliance.",
    icon: Gavel,
  },
  {
    id: "cor",
    label: "Research",
    description:
      "CO for academic research, data analysis, and publication with audit trails.",
    icon: Globe,
  },
  {
    id: "cocomp",
    label: "Compliance",
    description: "CO for regulatory audits with constrained AI assistants.",
    icon: Scale,
  },
  {
    id: "cof",
    label: "Finance",
    description:
      "CO for financial analysis with spending controls and approval workflows.",
    icon: Shield,
  },
];

// ---------------------------------------------------------------------------
// Constraint templates
// ---------------------------------------------------------------------------

interface ConstraintTemplate {
  id: string;
  label: string;
  description: string;
  financial: { max_spend: number };
  operational: { allowed_actions: string[]; blocked_actions: string[] };
  temporal: { max_duration_minutes: number };
}

const TEMPLATES: ConstraintTemplate[] = [
  {
    id: "strict",
    label: "Strict",
    description:
      "Tight constraints. Most actions require approval. Best for high-stakes work.",
    financial: { max_spend: 10 },
    operational: {
      allowed_actions: ["read", "analyze"],
      blocked_actions: ["write", "delete", "deploy", "execute", "communicate"],
    },
    temporal: { max_duration_minutes: 60 },
  },
  {
    id: "moderate",
    label: "Moderate",
    description:
      "Balanced constraints. Common actions are allowed, sensitive ones require approval.",
    financial: { max_spend: 100 },
    operational: {
      allowed_actions: ["read", "analyze", "write", "suggest"],
      blocked_actions: ["delete", "deploy", "communicate"],
    },
    temporal: { max_duration_minutes: 480 },
  },
  {
    id: "permissive",
    label: "Permissive",
    description:
      "Relaxed constraints. Most actions are allowed. Best for trusted, low-risk work.",
    financial: { max_spend: 1000 },
    operational: {
      allowed_actions: [
        "read",
        "analyze",
        "write",
        "suggest",
        "execute",
        "communicate",
      ],
      blocked_actions: ["delete", "deploy"],
    },
    temporal: { max_duration_minutes: 1440 },
  },
];

// ---------------------------------------------------------------------------
// Step components
// ---------------------------------------------------------------------------

function StepIndicator({
  currentStep,
  steps,
}: {
  currentStep: number;
  steps: string[];
}) {
  return (
    <div className="flex items-center gap-2">
      {steps.map((step, i) => (
        <div key={step} className="flex items-center gap-2">
          <div
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium",
              i < currentStep
                ? "bg-[var(--trust-auto)] text-white"
                : i === currentStep
                  ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
                  : "bg-[var(--muted)] text-[var(--muted-foreground)]",
            )}
          >
            {i < currentStep ? <Check className="h-4 w-4" /> : i + 1}
          </div>
          <span
            className={cn(
              "hidden text-sm sm:inline",
              i === currentStep
                ? "font-medium"
                : "text-[var(--muted-foreground)]",
            )}
          >
            {step}
          </span>
          {i < steps.length - 1 && (
            <div className="mx-1 h-px w-8 bg-[var(--border)]" />
          )}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function SessionWizardPage() {
  const navigate = useNavigate();
  const createSession = useCreateSession();

  const [step, setStep] = useState(0);
  const [workspaceId, setWorkspaceId] = useState("default");
  const [domain, setDomain] = useState("");
  const [template, setTemplate] = useState("");

  const steps = ["Name", "Domain", "Constraints", "Review"];
  const selectedDomain = DOMAINS.find((d) => d.id === domain);
  const selectedTemplate = TEMPLATES.find((t) => t.id === template);

  function canProceed(): boolean {
    switch (step) {
      case 0:
        return workspaceId.trim().length > 0;
      case 1:
        return domain.length > 0;
      case 2:
        return template.length > 0;
      case 3:
        return true;
      default:
        return false;
    }
  }

  async function handleCreate() {
    const tmpl = selectedTemplate;
    await createSession.mutateAsync({
      workspace_id: workspaceId.trim(),
      domain: domain || undefined,
      constraint_template: template || undefined,
      constraints: tmpl
        ? {
            financial: {
              max_spend: tmpl.financial.max_spend,
              current_spend: 0,
            },
            operational: {
              allowed_actions: tmpl.operational.allowed_actions,
              blocked_actions: tmpl.operational.blocked_actions,
            },
            temporal: {
              max_duration_minutes: tmpl.temporal.max_duration_minutes,
              elapsed_minutes: 0,
            },
            data_access: { allowed_paths: ["*"], blocked_paths: [] },
            communication: {
              allowed_channels: ["internal"],
              blocked_channels: [],
            },
          }
        : undefined,
    });
    navigate("/");
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Create a New Session
        </h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Set up a collaboration session with the right constraints for your
          work.
        </p>
      </div>

      {/* Progress */}
      <StepIndicator currentStep={step} steps={steps} />

      {/* Step content */}
      <Card>
        <CardContent>
          {/* Step 0: Name */}
          {step === 0 && (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="workspace">Workspace</Label>
                <Input
                  id="workspace"
                  placeholder="e.g. my-project"
                  value={workspaceId}
                  onChange={(e) => setWorkspaceId(e.target.value)}
                  autoFocus
                />
                <p className="text-xs text-[var(--muted-foreground)]">
                  A workspace groups related sessions together.
                </p>
              </div>
            </div>
          )}

          {/* Step 1: Domain */}
          {step === 1 && (
            <div className="grid gap-3 sm:grid-cols-2">
              {DOMAINS.map((d) => (
                <button
                  key={d.id}
                  type="button"
                  onClick={() => setDomain(d.id)}
                  className={cn(
                    "flex items-start gap-3 rounded-lg border-2 p-4 text-left transition-colors",
                    domain === d.id
                      ? "border-[var(--primary)] bg-[var(--accent)]"
                      : "border-[var(--border)] hover:border-[var(--muted-foreground)]",
                  )}
                >
                  <d.icon className="mt-0.5 h-5 w-5 shrink-0 text-[var(--muted-foreground)]" />
                  <div>
                    <p className="text-sm font-medium">{d.label}</p>
                    <p className="mt-0.5 text-xs text-[var(--muted-foreground)]">
                      {d.description}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Step 2: Template */}
          {step === 2 && (
            <div className="space-y-3">
              {TEMPLATES.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setTemplate(t.id)}
                  className={cn(
                    "w-full rounded-lg border-2 p-4 text-left transition-colors",
                    template === t.id
                      ? "border-[var(--primary)] bg-[var(--accent)]"
                      : "border-[var(--border)] hover:border-[var(--muted-foreground)]",
                  )}
                >
                  <p className="text-sm font-semibold">{t.label}</p>
                  <p className="mt-0.5 text-xs text-[var(--muted-foreground)]">
                    {t.description}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2 text-xs">
                    <span className="rounded-full bg-[var(--muted)] px-2 py-0.5">
                      Max spend: ${t.financial.max_spend}
                    </span>
                    <span className="rounded-full bg-[var(--muted)] px-2 py-0.5">
                      {t.operational.allowed_actions.length} allowed actions
                    </span>
                    <span className="rounded-full bg-[var(--muted)] px-2 py-0.5">
                      {t.temporal.max_duration_minutes}min max
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Step 3: Review */}
          {step === 3 && (
            <div className="space-y-4">
              <CardHeader className="px-0 pt-0">
                <CardTitle>Review your session</CardTitle>
              </CardHeader>
              <div className="space-y-3 rounded-lg border border-[var(--border)] p-4">
                <div>
                  <p className="text-xs font-medium text-[var(--muted-foreground)]">
                    Workspace
                  </p>
                  <p className="text-sm font-medium">{workspaceId}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-[var(--muted-foreground)]">
                    Domain
                  </p>
                  <p className="text-sm font-medium">
                    {selectedDomain?.label ?? "Not selected"}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-medium text-[var(--muted-foreground)]">
                    Constraint Template
                  </p>
                  <p className="text-sm font-medium">
                    {selectedTemplate?.label ?? "Not selected"}
                  </p>
                  {selectedTemplate && (
                    <p className="mt-0.5 text-xs text-[var(--muted-foreground)]">
                      {selectedTemplate.description}
                    </p>
                  )}
                </div>
              </div>

              {createSession.error && (
                <p className="text-sm text-[var(--trust-blocked)]">
                  Something went wrong creating the session. Please try again.
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={() => (step === 0 ? navigate("/") : setStep(step - 1))}
          disabled={createSession.isPending}
        >
          <ArrowLeft className="h-4 w-4" />
          {step === 0 ? "Cancel" : "Back"}
        </Button>

        {step < 3 ? (
          <Button onClick={() => setStep(step + 1)} disabled={!canProceed()}>
            Next
            <ArrowRight className="h-4 w-4" />
          </Button>
        ) : (
          <Button onClick={handleCreate} disabled={createSession.isPending}>
            {createSession.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Check className="h-4 w-4" />
                Create Session
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
