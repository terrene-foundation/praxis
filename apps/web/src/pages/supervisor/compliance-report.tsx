// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M11-13: Compliance Report
 *
 * Generate compliance reports for sessions:
 * - Template selector (domain-specific)
 * - Session picker (single or multi-session)
 * - Export: PDF, HTML, JSON
 */

import { useState } from "react";
import { Download, FileText, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useSessions, useExportBundle } from "@/services/hooks";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Report templates
// ---------------------------------------------------------------------------

interface ReportTemplate {
  id: string;
  label: string;
  description: string;
  sections: string[];
}

const REPORT_TEMPLATES: ReportTemplate[] = [
  {
    id: "coc-audit",
    label: "Software Development Audit",
    description:
      "Full audit trail of code generation decisions, constraint compliance, and trust chain verification.",
    sections: [
      "Session summary",
      "Decision log",
      "Constraint compliance",
      "Trust chain verification",
      "Held action audit",
    ],
  },
  {
    id: "education-assessment",
    label: "Learning Assessment",
    description:
      "Process-based assessment report showing deliberation quality and learning evidence.",
    sections: [
      "Session summary",
      "Deliberation log",
      "Process assessment",
      "Confidence progression",
    ],
  },
  {
    id: "governance-compliance",
    label: "Governance Compliance",
    description:
      "Constitutional compliance report showing decision alignment and constraint adherence.",
    sections: [
      "Session summary",
      "Decision log",
      "Constitutional alignment",
      "Constraint compliance",
      "Escalation audit",
    ],
  },
  {
    id: "general",
    label: "General Report",
    description: "Standard compliance report suitable for any domain.",
    sections: [
      "Session summary",
      "Timeline",
      "Constraint compliance",
      "Trust verification",
    ],
  },
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function ComplianceReportPage() {
  const { data: sessionData, isPending: sessionsLoading } = useSessions();
  const exportBundle = useExportBundle();

  const [template, setTemplate] = useState("");
  const [selectedSessions, setSelectedSessions] = useState<string[]>([]);
  const [format, setFormat] = useState<"pdf" | "html" | "json">("html");
  const [generating, setGenerating] = useState(false);

  const sessions = sessionData?.sessions ?? [];
  const selectedTemplate = REPORT_TEMPLATES.find((t) => t.id === template);

  function toggleSession(sessionId: string) {
    setSelectedSessions((prev) =>
      prev.includes(sessionId)
        ? prev.filter((id) => id !== sessionId)
        : [...prev, sessionId],
    );
  }

  async function handleGenerate() {
    if (selectedSessions.length === 0 || !template) return;

    setGenerating(true);
    try {
      // Export bundle for each selected session
      const bundles = await Promise.all(
        selectedSessions.map((id) => exportBundle.mutateAsync(id)),
      );

      // Build report content
      const report = {
        template: selectedTemplate,
        generated_at: new Date().toISOString(),
        format,
        sessions: bundles.map((bundle) => ({
          session_id: bundle.session_id,
          entries: bundle.entries.length,
          chain_length: bundle.chain_length,
        })),
      };

      if (format === "json") {
        // Download as JSON
        const blob = new Blob([JSON.stringify(report, null, 2)], {
          type: "application/json",
        });
        downloadBlob(blob, `compliance-report-${Date.now()}.json`);
      } else if (format === "html") {
        // Generate HTML report
        const html = generateHtmlReport(report, selectedTemplate);
        const blob = new Blob([html], { type: "text/html" });
        downloadBlob(blob, `compliance-report-${Date.now()}.html`);
      } else {
        // PDF: generate HTML and print
        const html = generateHtmlReport(report, selectedTemplate);
        const win = window.open("", "_blank");
        if (win) {
          win.document.write(html);
          win.document.close();
          win.print();
        }
      }
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Compliance Report</h1>
        <p className="text-sm text-[var(--muted-foreground)]">
          Generate a structured compliance report for one or more sessions.
        </p>
      </div>

      {/* Template selection */}
      <Card>
        <CardHeader>
          <CardTitle>Report Template</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {REPORT_TEMPLATES.map((t) => (
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
              <div className="mt-2 flex flex-wrap gap-1">
                {t.sections.map((section) => (
                  <span
                    key={section}
                    className="rounded-full bg-[var(--muted)] px-2 py-0.5 text-xs"
                  >
                    {section}
                  </span>
                ))}
              </div>
            </button>
          ))}
        </CardContent>
      </Card>

      {/* Session selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          {sessionsLoading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <div
                  key={i}
                  className="h-10 animate-pulse rounded bg-[var(--muted)]"
                />
              ))}
            </div>
          ) : sessions.length === 0 ? (
            <p className="py-4 text-center text-sm text-[var(--muted-foreground)]">
              No sessions available.
            </p>
          ) : (
            <div className="space-y-2">
              {sessions.map((session) => (
                <label
                  key={session.session_id}
                  className={cn(
                    "flex cursor-pointer items-center gap-3 rounded-md border p-3 transition-colors",
                    selectedSessions.includes(session.session_id)
                      ? "border-[var(--primary)] bg-[var(--accent)]"
                      : "border-[var(--border)] hover:bg-[var(--accent)]",
                  )}
                >
                  <input
                    type="checkbox"
                    checked={selectedSessions.includes(session.session_id)}
                    onChange={() => toggleSession(session.session_id)}
                    className="h-4 w-4 accent-[var(--primary)]"
                  />
                  <div>
                    <p className="text-sm font-medium capitalize">
                      {session.domain} session
                    </p>
                    <p className="text-xs text-[var(--muted-foreground)]">
                      {session.state} | {session.session_id.slice(0, 12)}...
                    </p>
                  </div>
                </label>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Format selection */}
      <Card>
        <CardHeader>
          <CardTitle>Export Format</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            {(["html", "pdf", "json"] as const).map((fmt) => (
              <button
                key={fmt}
                type="button"
                onClick={() => setFormat(fmt)}
                className={cn(
                  "flex items-center gap-2 rounded-md border-2 px-4 py-2 text-sm font-medium transition-colors",
                  format === fmt
                    ? "border-[var(--primary)] bg-[var(--accent)]"
                    : "border-[var(--border)] hover:border-[var(--muted-foreground)]",
                )}
              >
                <FileText className="h-4 w-4" />
                {fmt.toUpperCase()}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Generate */}
      <div className="flex justify-end">
        <Button
          onClick={handleGenerate}
          disabled={!template || selectedSessions.length === 0 || generating}
          size="lg"
        >
          {generating ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Download className="h-4 w-4" />
              Generate Report
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function generateHtmlReport(
  report: Record<string, unknown>,
  template?: ReportTemplate,
): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Compliance Report — Praxis</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }
    h1 { font-size: 1.5rem; border-bottom: 2px solid #e5e5e5; padding-bottom: 0.5rem; }
    h2 { font-size: 1.1rem; color: #555; margin-top: 1.5rem; }
    .meta { color: #888; font-size: 0.85rem; }
    .section { margin: 1rem 0; padding: 1rem; border: 1px solid #e5e5e5; border-radius: 0.5rem; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; background: #f0f0f0; }
    pre { background: #f8f8f8; padding: 1rem; border-radius: 0.5rem; overflow: auto; font-size: 0.8rem; }
    footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e5e5; font-size: 0.75rem; color: #999; }
  </style>
</head>
<body>
  <h1>Compliance Report</h1>
  <p class="meta">Template: ${template?.label ?? "General"} | Generated: ${new Date().toLocaleString()}</p>

  ${
    template?.sections
      .map(
        (section) => `
  <div class="section">
    <h2>${section}</h2>
    <p>Report data for this section will be populated from session analysis.</p>
  </div>`,
      )
      .join("") ?? ""
  }

  <h2>Raw Data</h2>
  <pre>${JSON.stringify(report, null, 2)}</pre>

  <footer>
    Generated by Praxis — Terrene Foundation open-source CO platform.
  </footer>
</body>
</html>`;
}
