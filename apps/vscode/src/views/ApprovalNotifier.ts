// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Held action approval notification system.
 *
 * Polls the Praxis server for pending held actions and shows VS Code
 * warning notifications when new ones appear. Each notification has
 * "Approve" and "View Details" buttons. The detail view opens a
 * webview panel showing the full action context, constraint info,
 * and approve/deny controls.
 */

import * as vscode from "vscode";
import { PraxisClient } from "../api/client";
import type { HeldAction } from "../api/types";

export class ApprovalNotifier {
  private client: PraxisClient;
  private extensionUri: vscode.Uri;
  private pollTimer?: ReturnType<typeof setInterval>;
  /** IDs of held actions the user has already been notified about. */
  private seenIds: Set<string> = new Set();

  constructor(client: PraxisClient, extensionUri: vscode.Uri) {
    this.client = client;
    this.extensionUri = extensionUri;
  }

  /** Start polling for new held actions. */
  startPolling(): void {
    const cfg = vscode.workspace.getConfiguration("praxis");
    const seconds = cfg.get<number>("pollIntervalSeconds") ?? 30;
    this.pollTimer = setInterval(() => this.check(), seconds * 1000);
    // Immediate first check
    this.check();
  }

  /** Stop polling. */
  stopPolling(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = undefined;
    }
  }

  dispose(): void {
    this.stopPolling();
  }

  // -------------------------------------------------------------------
  // Polling
  // -------------------------------------------------------------------

  private async check(): Promise<void> {
    try {
      const listRes = await this.client.listSessions();
      const active = listRes.sessions.find((s) => s.state === "active");
      if (!active) {
        return;
      }

      const heldRes = await this.client.getHeldActions(active.session_id);
      for (const action of heldRes.held_actions) {
        if (!this.seenIds.has(action.held_id)) {
          this.seenIds.add(action.held_id);
          this.showNotification(active.session_id, action);
        }
      }
    } catch {
      // Server unreachable or no active session — silently skip
    }
  }

  // -------------------------------------------------------------------
  // Notification
  // -------------------------------------------------------------------

  private showNotification(sessionId: string, action: HeldAction): void {
    const description = action.action
      ? `${action.action} (${action.dimension})`
      : action.reason;

    vscode.window
      .showWarningMessage(
        `Praxis: Action requires approval \u2014 ${description}`,
        "Approve",
        "View Details",
      )
      .then((choice) => {
        if (choice === "Approve") {
          this.approve(sessionId, action);
        } else if (choice === "View Details") {
          this.showDetailPanel(sessionId, action);
        }
      });
  }

  private async approve(sessionId: string, action: HeldAction): Promise<void> {
    try {
      await this.client.approveAction(sessionId, action.held_id);
      vscode.window.showInformationMessage(
        `Held action approved: ${action.held_id.slice(0, 8)}`,
      );
    } catch (err) {
      vscode.window.showErrorMessage(
        `Failed to approve action: ${err instanceof Error ? err.message : String(err)}`,
      );
    }
  }

  // -------------------------------------------------------------------
  // Detail panel
  // -------------------------------------------------------------------

  private showDetailPanel(sessionId: string, action: HeldAction): void {
    const panel = vscode.window.createWebviewPanel(
      "praxis.heldActionDetail",
      `Held Action: ${action.held_id.slice(0, 8)}`,
      vscode.ViewColumn.One,
      {
        enableScripts: true,
        localResourceRoots: [this.extensionUri],
      },
    );

    const nonce = getNonce();

    panel.webview.html = /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta
    http-equiv="Content-Security-Policy"
    content="default-src 'none'; style-src 'nonce-${nonce}'; script-src 'nonce-${nonce}';"
  />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style nonce="${nonce}">
    body {
      font-family: var(--vscode-font-family);
      font-size: var(--vscode-font-size);
      color: var(--vscode-foreground);
      padding: 16px;
      max-width: 600px;
      margin: 0 auto;
    }
    h2 { margin-top: 0; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
    td { padding: 6px 8px; border-bottom: 1px solid var(--vscode-widget-border); font-size: 13px; }
    td:first-child { font-weight: bold; width: 140px; color: var(--vscode-descriptionForeground); }
    .actions { display: flex; gap: 8px; margin-top: 16px; }
    button {
      background: var(--vscode-button-background); color: var(--vscode-button-foreground);
      border: none; padding: 8px 16px; cursor: pointer; border-radius: 2px; font-size: 13px;
    }
    button:hover { background: var(--vscode-button-hoverBackground); }
    button.danger { background: var(--vscode-editorError-foreground); }
    .feedback { padding: 8px; border-radius: 4px; margin-top: 12px; font-size: 13px; }
    .feedback.success { background: var(--vscode-testing-iconPassed); color: #fff; }
    .feedback.error { background: var(--vscode-editorError-foreground); color: #fff; }
    .warn-banner { background: var(--vscode-editorWarning-foreground); color: #fff; padding: 8px; border-radius: 4px; margin-bottom: 16px; }
  </style>
</head>
<body>
  <div class="warn-banner">This action is held pending human approval.</div>

  <h2>Held Action Details</h2>
  <table>
    <tr><td>Action ID</td><td>${escapeHtml(action.held_id)}</td></tr>
    <tr><td>Session</td><td>${escapeHtml(sessionId).slice(0, 16)}...</td></tr>
    <tr><td>Action</td><td>${escapeHtml(action.action)}</td></tr>
    <tr><td>Resource</td><td>${escapeHtml(action.resource)}</td></tr>
    <tr><td>Dimension</td><td>${escapeHtml(action.dimension)}</td></tr>
    <tr><td>Reason</td><td>${escapeHtml(action.reason)}</td></tr>
    <tr><td>Utilization</td><td>${Math.round(action.utilization * 100)}%</td></tr>
    <tr><td>Created</td><td>${escapeHtml(action.created_at)}</td></tr>
  </table>

  <div class="actions">
    <button onclick="resolve('approve')">Approve</button>
    <button class="danger" onclick="resolve('deny')">Deny</button>
  </div>

  <div id="feedback"></div>

  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    function resolve(action) {
      vscode.postMessage({ command: action });
    }
    window.addEventListener('message', function(event) {
      const msg = event.data;
      if (msg.command === 'result') {
        const el = document.getElementById('feedback');
        if (!el) return;
        el.className = 'feedback ' + (msg.success ? 'success' : 'error');
        el.textContent = msg.success ? 'Action resolved.' : ('Error: ' + msg.error);
      }
    });
  </script>
</body>
</html>`;

    panel.webview.onDidReceiveMessage(async (msg) => {
      if (msg.command === "approve") {
        try {
          await this.client.approveAction(sessionId, action.held_id);
          panel.webview.postMessage({
            command: "result",
            success: true,
          });
        } catch (err) {
          panel.webview.postMessage({
            command: "result",
            success: false,
            error: err instanceof Error ? err.message : String(err),
          });
        }
      } else if (msg.command === "deny") {
        try {
          await this.client.denyAction(sessionId, action.held_id);
          panel.webview.postMessage({
            command: "result",
            success: true,
          });
        } catch (err) {
          panel.webview.postMessage({
            command: "result",
            success: false,
            error: err instanceof Error ? err.message : String(err),
          });
        }
      }
    });
  }
}

// -------------------------------------------------------------------
// Helpers
// -------------------------------------------------------------------

function getNonce(): string {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "";
  for (let i = 0; i < 32; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
