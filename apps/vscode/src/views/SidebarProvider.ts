// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Webview-based sidebar for Praxis session management.
 *
 * Displays active sessions, constraint summaries, recent decisions,
 * and held action counts. Polls the Praxis server at a configurable
 * interval (default 30 s) and re-renders the webview on each tick.
 */

import * as vscode from "vscode";
import { PraxisClient } from "../api/client";
import type {
  ConstraintEnvelope,
  DeliberationRecord,
  GradientDimension,
  HeldAction,
  Session,
} from "../api/types";

/**
 * Snapshot of data displayed in the sidebar.
 *
 * Populated by polling the Praxis REST API. When the server is
 * unreachable the `offline` flag is set and partial data may be stale.
 */
interface SidebarState {
  sessions: Session[];
  activeSession: Session | null;
  gradient: Record<string, GradientDimension> | GradientDimension[];
  recentDecisions: DeliberationRecord[];
  heldActions: HeldAction[];
  heldCount: number;
  offline: boolean;
  errorMessage: string;
}

export class SidebarProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = "praxis.sessionView";

  private view?: vscode.WebviewView;
  private client: PraxisClient;
  private pollTimer?: ReturnType<typeof setInterval>;
  private state: SidebarState = {
    sessions: [],
    activeSession: null,
    gradient: [],
    recentDecisions: [],
    heldActions: [],
    heldCount: 0,
    offline: true,
    errorMessage: "",
  };

  constructor(
    private readonly extensionUri: vscode.Uri,
    client: PraxisClient,
  ) {
    this.client = client;
  }

  // -------------------------------------------------------------------
  // WebviewViewProvider
  // -------------------------------------------------------------------

  resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken,
  ): void {
    this.view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this.extensionUri],
    };

    // Handle messages from the webview
    webviewView.webview.onDidReceiveMessage((msg) => this.handleMessage(msg));

    // Initial render + start polling
    this.refresh();
    this.startPolling();

    webviewView.onDidDispose(() => {
      this.stopPolling();
    });
  }

  // -------------------------------------------------------------------
  // Polling
  // -------------------------------------------------------------------

  private startPolling(): void {
    const cfg = vscode.workspace.getConfiguration("praxis");
    const seconds = cfg.get<number>("pollIntervalSeconds") ?? 30;
    this.pollTimer = setInterval(() => this.refresh(), seconds * 1000);
  }

  private stopPolling(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = undefined;
    }
  }

  /** Fetch latest data from the server and re-render. */
  async refresh(): Promise<void> {
    try {
      const listRes = await this.client.listSessions();
      this.state.sessions = listRes.sessions;
      this.state.offline = false;
      this.state.errorMessage = "";

      // Pick the first active session as the "current" one
      const active =
        this.state.sessions.find((s) => s.state === "active") ?? null;
      this.state.activeSession = active;

      if (active) {
        // Fetch gradient, timeline, and held actions in parallel
        const [gradientRes, timelineRes, heldRes] = await Promise.all([
          this.client.getGradient(active.session_id).catch(() => null),
          this.client.getTimeline(active.session_id).catch(() => null),
          this.client.getHeldActions(active.session_id).catch(() => null),
        ]);

        if (gradientRes) {
          this.state.gradient = gradientRes.dimensions;
        }
        if (timelineRes) {
          this.state.recentDecisions = timelineRes.records.slice(0, 5);
        }
        if (heldRes) {
          this.state.heldActions = heldRes.held_actions;
          this.state.heldCount = heldRes.total;
        }
      } else {
        this.state.gradient = [];
        this.state.recentDecisions = [];
        this.state.heldActions = [];
        this.state.heldCount = 0;
      }
    } catch (err) {
      this.state.offline = true;
      this.state.errorMessage =
        err instanceof Error ? err.message : String(err);
    }

    this.render();
  }

  // -------------------------------------------------------------------
  // Webview message handling
  // -------------------------------------------------------------------

  private async handleMessage(msg: {
    command: string;
    [key: string]: unknown;
  }): Promise<void> {
    switch (msg.command) {
      case "startSession": {
        const workspace = (msg.workspace as string) || "default";
        const domain = (msg.domain as string) || "coc";
        const template = (msg.template as string) || "moderate";
        try {
          await this.client.createSession(workspace, domain, template);
          await this.refresh();
        } catch (err) {
          vscode.window.showErrorMessage(
            `Failed to start session: ${err instanceof Error ? err.message : String(err)}`,
          );
        }
        break;
      }
      case "endSession": {
        const sessionId = msg.sessionId as string;
        if (!sessionId) {
          return;
        }
        try {
          await this.client.endSession(sessionId);
          await this.refresh();
        } catch (err) {
          vscode.window.showErrorMessage(
            `Failed to end session: ${err instanceof Error ? err.message : String(err)}`,
          );
        }
        break;
      }
      case "pauseSession": {
        const sid = msg.sessionId as string;
        if (!sid) {
          return;
        }
        try {
          await this.client.pauseSession(sid);
          await this.refresh();
        } catch (err) {
          vscode.window.showErrorMessage(
            `Failed to pause session: ${err instanceof Error ? err.message : String(err)}`,
          );
        }
        break;
      }
      case "resumeSession": {
        const sid = msg.sessionId as string;
        if (!sid) {
          return;
        }
        try {
          await this.client.resumeSession(sid);
          await this.refresh();
        } catch (err) {
          vscode.window.showErrorMessage(
            `Failed to resume session: ${err instanceof Error ? err.message : String(err)}`,
          );
        }
        break;
      }
      case "refresh":
        await this.refresh();
        break;
      case "openDecisionForm":
        vscode.commands.executeCommand("praxis.recordDecision");
        break;
    }
  }

  // -------------------------------------------------------------------
  // Rendering
  // -------------------------------------------------------------------

  private render(): void {
    if (!this.view) {
      return;
    }
    this.view.webview.html = this.buildHtml();
  }

  /**
   * Build the full HTML for the sidebar webview.
   *
   * Uses VS Code CSS variables so the panel matches the current theme
   * without shipping a custom stylesheet.
   */
  private buildHtml(): string {
    const { sessions, activeSession, offline, heldCount } = this.state;
    const nonce = getNonce();

    // -- Session list rows --
    let sessionListHtml = "";
    if (sessions.length === 0) {
      sessionListHtml = `<p class="muted">No sessions found.</p>`;
    } else {
      sessionListHtml = sessions
        .map((s) => {
          const badge = stateBadge(s.state);
          const actions =
            s.state === "active"
              ? `<button class="small" onclick="send('pauseSession','${s.session_id}')">Pause</button>
                 <button class="small danger" onclick="send('endSession','${s.session_id}')">End</button>`
              : s.state === "paused"
                ? `<button class="small" onclick="send('resumeSession','${s.session_id}')">Resume</button>`
                : "";
          return `
            <div class="session-row">
              <span class="session-id" title="${s.session_id}">${s.session_id.slice(0, 8)}</span>
              ${badge}
              <span class="domain">${s.domain}</span>
              <span class="actions">${actions}</span>
            </div>`;
        })
        .join("");
    }

    // -- Constraint gradient --
    let constraintHtml = "";
    if (activeSession) {
      const dims = normalizeGradient(this.state.gradient);
      if (dims.length > 0) {
        constraintHtml = dims
          .map((d) => {
            const pct = Math.round(d.utilization * 100);
            const cls = pct > 70 ? "warn" : pct > 90 ? "critical" : "";
            return `<div class="constraint-row ${cls}">
              <span>${d.dimension}</span>
              <span>${pct}%</span>
            </div>`;
          })
          .join("");
      } else {
        constraintHtml = `<p class="muted">No constraint data.</p>`;
      }
    }

    // -- Recent decisions --
    let decisionsHtml = "";
    if (this.state.recentDecisions.length > 0) {
      decisionsHtml = this.state.recentDecisions
        .map(
          (r) =>
            `<div class="decision-row">
              <span class="type">${r.record_type}</span>
              <span class="content">${escapeHtml(r.content).slice(0, 80)}</span>
            </div>`,
        )
        .join("");
    } else if (activeSession) {
      decisionsHtml = `<p class="muted">No decisions recorded yet.</p>`;
    }

    // -- Held actions --
    const heldBadge =
      heldCount > 0
        ? `<span class="badge warn">${heldCount} pending</span>`
        : `<span class="badge">0</span>`;

    return /* html */ `<!DOCTYPE html>
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
      padding: 8px;
      margin: 0;
    }
    h3 { margin: 12px 0 6px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--vscode-descriptionForeground); }
    .muted { color: var(--vscode-descriptionForeground); font-style: italic; font-size: 12px; }
    .badge { display: inline-block; padding: 1px 6px; border-radius: 8px; font-size: 11px; background: var(--vscode-badge-background); color: var(--vscode-badge-foreground); }
    .badge.warn { background: var(--vscode-editorWarning-foreground); color: #fff; }
    .session-row { display: flex; align-items: center; gap: 6px; padding: 4px 0; border-bottom: 1px solid var(--vscode-widget-border); flex-wrap: wrap; }
    .session-id { font-family: var(--vscode-editor-font-family); font-size: 12px; }
    .domain { font-size: 11px; color: var(--vscode-descriptionForeground); }
    .actions { margin-left: auto; display: flex; gap: 4px; }
    .state-badge { font-size: 10px; padding: 1px 5px; border-radius: 4px; }
    .state-active { background: var(--vscode-testing-iconPassed); color: #fff; }
    .state-paused { background: var(--vscode-editorWarning-foreground); color: #fff; }
    .state-ended { background: var(--vscode-descriptionForeground); color: #fff; }
    .constraint-row { display: flex; justify-content: space-between; padding: 2px 0; font-size: 12px; }
    .constraint-row.warn { color: var(--vscode-editorWarning-foreground); }
    .constraint-row.critical { color: var(--vscode-editorError-foreground); font-weight: bold; }
    .decision-row { padding: 2px 0; font-size: 12px; border-bottom: 1px solid var(--vscode-widget-border); }
    .decision-row .type { font-weight: bold; margin-right: 4px; }
    .decision-row .content { color: var(--vscode-descriptionForeground); }
    button { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; padding: 4px 8px; cursor: pointer; border-radius: 2px; font-size: 12px; }
    button:hover { background: var(--vscode-button-hoverBackground); }
    button.small { padding: 2px 6px; font-size: 11px; }
    button.danger { background: var(--vscode-editorError-foreground); }
    .offline-banner { background: var(--vscode-editorError-foreground); color: #fff; padding: 6px 8px; border-radius: 4px; margin-bottom: 8px; font-size: 12px; }
    .form-group { margin: 6px 0; }
    .form-group label { display: block; font-size: 11px; margin-bottom: 2px; color: var(--vscode-descriptionForeground); }
    .form-group input, .form-group select { width: 100%; box-sizing: border-box; padding: 4px 6px; background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); border-radius: 2px; font-size: 12px; }
    .toolbar { display: flex; gap: 4px; margin: 8px 0; flex-wrap: wrap; }
  </style>
</head>
<body>
  ${offline ? `<div class="offline-banner">Server unreachable</div>` : ""}

  <div class="toolbar">
    <button onclick="toggleNewSession()">New Session</button>
    <button onclick="send('openDecisionForm')">Record Decision</button>
    <button onclick="send('refresh')">Refresh</button>
  </div>

  <div id="newSessionForm" style="display:none;">
    <div class="form-group">
      <label for="ws">Workspace</label>
      <input id="ws" type="text" value="default" />
    </div>
    <div class="form-group">
      <label for="domain">Domain</label>
      <select id="domain">
        <option value="coc">COC (Codegen)</option>
        <option value="coe">COE (Education)</option>
        <option value="cog">COG (Governance)</option>
      </select>
    </div>
    <div class="form-group">
      <label for="template">Constraint Template</label>
      <select id="template">
        <option value="moderate">Moderate</option>
        <option value="strict">Strict</option>
        <option value="permissive">Permissive</option>
      </select>
    </div>
    <button onclick="submitNewSession()">Create</button>
  </div>

  <h3>Sessions</h3>
  ${sessionListHtml}

  ${
    activeSession
      ? `
    <h3>Constraints</h3>
    ${constraintHtml}

    <h3>Recent Decisions</h3>
    ${decisionsHtml}

    <h3>Held Actions ${heldBadge}</h3>
    ${
      this.state.heldActions.length > 0
        ? this.state.heldActions
            .map(
              (h) =>
                `<div class="decision-row">
                  <span class="type">${escapeHtml(h.dimension)}</span>
                  <span class="content">${escapeHtml(h.reason).slice(0, 60)}</span>
                </div>`,
            )
            .join("")
        : `<p class="muted">No held actions.</p>`
    }
  `
      : ""
  }

  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    function send(command, sessionId) {
      vscode.postMessage({ command, sessionId });
    }
    function toggleNewSession() {
      const el = document.getElementById('newSessionForm');
      if (el) { el.style.display = el.style.display === 'none' ? 'block' : 'none'; }
    }
    function submitNewSession() {
      const ws = document.getElementById('ws');
      const domain = document.getElementById('domain');
      const template = document.getElementById('template');
      vscode.postMessage({
        command: 'startSession',
        workspace: ws ? ws.value : 'default',
        domain: domain ? domain.value : 'coc',
        template: template ? template.value : 'moderate',
      });
      const el = document.getElementById('newSessionForm');
      if (el) { el.style.display = 'none'; }
    }
  </script>
</body>
</html>`;
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

function stateBadge(state: string): string {
  return `<span class="state-badge state-${state}">${state}</span>`;
}

/** Normalize the gradient response into a flat array. */
function normalizeGradient(
  gradient: Record<string, GradientDimension> | GradientDimension[],
): GradientDimension[] {
  if (Array.isArray(gradient)) {
    return gradient;
  }
  return Object.entries(gradient).map(([key, val]) => ({
    dimension: val.dimension || key,
    utilization: val.utilization ?? 0,
    status: val.status ?? "ok",
  }));
}
