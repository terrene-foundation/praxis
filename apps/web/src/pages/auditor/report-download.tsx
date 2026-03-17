// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M12-06: Report Download
 *
 * Client-side report generation from bundle data:
 * - PDF generation (via browser print)
 * - HTML export
 * - JSON export
 * - Auditor assessment fields included
 */

import { useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { ArrowLeft, Download, FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import type { VerificationBundle } from "@/types/api";
import type { ChainVerificationResult } from "@/lib/chain-verifier";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function ReportDownloadPage() {
  const location = useLocation();
  const navigate = useNavigate();

  const state = location.state as {
    bundle?: VerificationBundle;
    result?: ChainVerificationResult;
  } | null;
  const bundle = state?.bundle;
  const result = state?.result;

  const [auditorName, setAuditorName] = useState("");
  const [auditorNotes, setAuditorNotes] = useState("");
  const [format, setFormat] = useState<"html" | "json" | "pdf">("html");

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

  function generateReport() {
    const reportData = {
      generated_at: new Date().toISOString(),
      auditor: auditorName || "Anonymous",
      auditor_notes: auditorNotes,
      session_id: bundle!.session_id,
      chain_length: bundle!.chain_length,
      verification: result
        ? {
            valid: result.valid,
            total_entries: result.totalEntries,
            verified_entries: result.verifiedEntries,
            breaks: result.breaks,
          }
        : null,
      entries_count: bundle!.entries.length,
    };

    if (format === "json") {
      const blob = new Blob([JSON.stringify(reportData, null, 2)], {
        type: "application/json",
      });
      downloadBlob(blob, `audit-report-${bundle!.session_id.slice(0, 8)}.json`);
    } else {
      const html = buildHtmlReport(reportData);
      if (format === "pdf") {
        const win = window.open("", "_blank");
        if (win) {
          win.document.write(html);
          win.document.close();
          win.print();
        }
      } else {
        const blob = new Blob([html], { type: "text/html" });
        downloadBlob(
          blob,
          `audit-report-${bundle!.session_id.slice(0, 8)}.html`,
        );
      }
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-4 md:p-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Download Report</h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            Generate an audit report from the verified bundle.
          </p>
        </div>
      </div>

      {/* Auditor fields */}
      <Card>
        <CardHeader>
          <CardTitle>Auditor Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="auditor-name">Your Name (optional)</Label>
            <input
              id="auditor-name"
              value={auditorName}
              onChange={(e) => setAuditorName(e.target.value)}
              placeholder="e.g. Jane Auditor"
              className="h-9 w-full rounded-md border border-[var(--input)] bg-transparent px-3 text-sm shadow-xs outline-none placeholder:text-[var(--muted-foreground)] focus-visible:border-[var(--ring)]"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="auditor-notes">Assessment Notes (optional)</Label>
            <textarea
              id="auditor-notes"
              value={auditorNotes}
              onChange={(e) => setAuditorNotes(e.target.value)}
              placeholder="Add any notes about your assessment..."
              rows={3}
              className="w-full rounded-md border border-[var(--input)] bg-transparent px-3 py-2 text-sm shadow-xs outline-none placeholder:text-[var(--muted-foreground)] focus-visible:border-[var(--ring)]"
            />
          </div>
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

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Report Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-[var(--muted-foreground)]">Session</span>
            <span className="font-mono">
              {bundle.session_id.slice(0, 16)}...
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-[var(--muted-foreground)]">
              Chain entries
            </span>
            <span>{bundle.entries.length}</span>
          </div>
          {result && (
            <>
              <div className="flex justify-between">
                <span className="text-[var(--muted-foreground)]">
                  Chain valid
                </span>
                <span
                  className={result.valid ? "trust-valid" : "trust-invalid"}
                >
                  {result.valid ? "Yes" : "No"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--muted-foreground)]">
                  Verified entries
                </span>
                <span>
                  {result.verifiedEntries} / {result.totalEntries}
                </span>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Download */}
      <div className="flex justify-end">
        <Button size="lg" onClick={generateReport}>
          <Download className="h-4 w-4" />
          Download {format.toUpperCase()} Report
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

function buildHtmlReport(data: Record<string, unknown>): string {
  const v = data.verification as Record<string, unknown> | null;
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Audit Report — Praxis</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }
    h1 { font-size: 1.5rem; border-bottom: 2px solid #e5e5e5; padding-bottom: 0.5rem; }
    h2 { font-size: 1.1rem; color: #555; margin-top: 1.5rem; }
    .meta { color: #888; font-size: 0.85rem; }
    .section { margin: 1rem 0; padding: 1rem; border: 1px solid #e5e5e5; border-radius: 0.5rem; }
    .valid { color: #22c55e; font-weight: 600; }
    .invalid { color: #ef4444; font-weight: 600; }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; padding: 0.5rem; border-bottom: 1px solid #e5e5e5; }
    footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e5e5; font-size: 0.75rem; color: #999; }
  </style>
</head>
<body>
  <h1>Audit Report</h1>
  <p class="meta">
    Auditor: ${data.auditor as string} |
    Generated: ${new Date(data.generated_at as string).toLocaleString()} |
    Session: ${(data.session_id as string).slice(0, 16)}...
  </p>

  <div class="section">
    <h2>Chain Verification</h2>
    <table>
      <tr><td>Chain valid</td><td class="${v?.valid ? "valid" : "invalid"}">${v?.valid ? "Yes" : "No"}</td></tr>
      <tr><td>Total entries</td><td>${v?.total_entries ?? "N/A"}</td></tr>
      <tr><td>Verified entries</td><td>${v?.verified_entries ?? "N/A"}</td></tr>
      <tr><td>Chain length</td><td>${data.chain_length}</td></tr>
    </table>
  </div>

  ${
    (data.auditor_notes as string)
      ? `<div class="section">
    <h2>Auditor Notes</h2>
    <p>${data.auditor_notes as string}</p>
  </div>`
      : ""
  }

  <footer>
    Generated by Praxis Verification Portal — Terrene Foundation open-source CO platform.
    All verification was performed client-side. No data was sent to any server.
  </footer>
</body>
</html>`;
}
