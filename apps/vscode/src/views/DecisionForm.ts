// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Webview panel for recording deliberation decisions.
 *
 * Opened by the `praxis.recordDecision` command. Collects decision
 * text, rationale, alternatives, and confidence, then submits to
 * the active session via the Praxis API.
 */

import * as vscode from "vscode";
import { PraxisClient } from "../api/client";

/**
 * Show the decision recording form as a webview panel.
 *
 * If no active session exists, shows an error message instead.
 */
export async function showDecisionForm(
  client: PraxisClient,
  extensionUri: vscode.Uri,
): Promise<void> {
  // Determine the active session
  let activeSessionId: string | undefined;
  try {
    const listRes = await client.listSessions();
    const active = listRes.sessions.find((s) => s.state === "active");
    if (active) {
      activeSessionId = active.session_id;
    }
  } catch {
    // Will show error below
  }

  if (!activeSessionId) {
    vscode.window.showErrorMessage(
      "No active Praxis session. Start a session first.",
    );
    return;
  }

  const panel = vscode.window.createWebviewPanel(
    "praxis.decisionForm",
    "Record Decision",
    vscode.ViewColumn.One,
    {
      enableScripts: true,
      localResourceRoots: [extensionUri],
    },
  );

  const nonce = getNonce();
  const sessionIdShort = activeSessionId.slice(0, 8);

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
    .form-group { margin-bottom: 12px; }
    .form-group label { display: block; margin-bottom: 4px; font-weight: bold; font-size: 12px; color: var(--vscode-descriptionForeground); }
    input, textarea, select {
      width: 100%; box-sizing: border-box; padding: 6px 8px;
      background: var(--vscode-input-background); color: var(--vscode-input-foreground);
      border: 1px solid var(--vscode-input-border); border-radius: 2px; font-size: 13px;
      font-family: var(--vscode-font-family);
    }
    textarea { resize: vertical; min-height: 60px; }
    .alternatives-list { margin: 4px 0; }
    .alt-row { display: flex; gap: 4px; margin-bottom: 4px; }
    .alt-row input { flex: 1; }
    .alt-row button { flex-shrink: 0; }
    button {
      background: var(--vscode-button-background); color: var(--vscode-button-foreground);
      border: none; padding: 6px 14px; cursor: pointer; border-radius: 2px; font-size: 13px;
    }
    button:hover { background: var(--vscode-button-hoverBackground); }
    button.secondary {
      background: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
    }
    button.small { padding: 3px 8px; font-size: 11px; }
    .slider-group { display: flex; align-items: center; gap: 8px; }
    .slider-group input[type="range"] { flex: 1; }
    .slider-group span { min-width: 36px; text-align: right; font-size: 13px; }
    .feedback { padding: 8px; border-radius: 4px; margin-top: 12px; font-size: 13px; }
    .feedback.success { background: var(--vscode-testing-iconPassed); color: #fff; }
    .feedback.error { background: var(--vscode-editorError-foreground); color: #fff; }
    .muted { color: var(--vscode-descriptionForeground); font-size: 12px; }
  </style>
</head>
<body>
  <h2>Record Decision</h2>
  <p class="muted">Session: ${sessionIdShort}...</p>

  <div class="form-group">
    <label for="decisionType">Decision Type</label>
    <select id="decisionType">
      <option value="architecture">Architecture</option>
      <option value="implementation">Implementation</option>
      <option value="constraint">Constraint change</option>
      <option value="approval">Approval / override</option>
      <option value="other">Other</option>
    </select>
  </div>

  <div class="form-group">
    <label for="decision">Decision *</label>
    <textarea id="decision" rows="3" placeholder="What was decided?"></textarea>
  </div>

  <div class="form-group">
    <label for="rationale">Rationale *</label>
    <textarea id="rationale" rows="3" placeholder="Why was this decision made?"></textarea>
  </div>

  <div class="form-group">
    <label>Alternatives considered</label>
    <div id="altList" class="alternatives-list"></div>
    <button class="small secondary" onclick="addAlternative()">+ Add alternative</button>
  </div>

  <div class="form-group">
    <label for="confidence">Confidence</label>
    <div class="slider-group">
      <input type="range" id="confidence" min="0" max="100" value="70" oninput="updateSlider()" />
      <span id="confVal">70%</span>
    </div>
  </div>

  <button onclick="submit()">Submit Decision</button>

  <div id="feedback"></div>

  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    let altCount = 0;

    function updateSlider() {
      const slider = document.getElementById('confidence');
      const label = document.getElementById('confVal');
      if (slider && label) { label.textContent = slider.value + '%'; }
    }

    function addAlternative() {
      altCount++;
      const list = document.getElementById('altList');
      if (!list) return;
      const row = document.createElement('div');
      row.className = 'alt-row';
      row.id = 'alt-' + altCount;
      row.innerHTML = '<input type="text" placeholder="Alternative option..." />'
        + '<button class="small secondary" onclick="removeAlt(' + altCount + ')">x</button>';
      list.appendChild(row);
    }

    function removeAlt(id) {
      const row = document.getElementById('alt-' + id);
      if (row) row.remove();
    }

    function submit() {
      const decision = document.getElementById('decision');
      const rationale = document.getElementById('rationale');
      const confidence = document.getElementById('confidence');
      const decisionType = document.getElementById('decisionType');

      if (!decision || !decision.value.trim()) {
        showFeedback('Decision text is required.', true);
        return;
      }
      if (!rationale || !rationale.value.trim()) {
        showFeedback('Rationale is required.', true);
        return;
      }

      const altInputs = document.querySelectorAll('#altList input[type="text"]');
      const alternatives = [];
      altInputs.forEach(function(input) {
        if (input.value.trim()) alternatives.push(input.value.trim());
      });

      const prefix = decisionType ? '[' + decisionType.value + '] ' : '';

      vscode.postMessage({
        command: 'submitDecision',
        decision: prefix + decision.value.trim(),
        rationale: rationale.value.trim(),
        alternatives: alternatives,
        confidence: confidence ? parseInt(confidence.value, 10) : 70,
      });
    }

    function showFeedback(msg, isError) {
      const el = document.getElementById('feedback');
      if (!el) return;
      el.className = 'feedback ' + (isError ? 'error' : 'success');
      el.textContent = msg;
    }

    window.addEventListener('message', function(event) {
      const msg = event.data;
      if (msg.command === 'result') {
        showFeedback(msg.success ? 'Decision recorded.' : ('Error: ' + msg.error), !msg.success);
      }
    });
  </script>
</body>
</html>`;

  // Handle messages from the form
  panel.webview.onDidReceiveMessage(async (msg) => {
    if (msg.command === "submitDecision" && activeSessionId) {
      try {
        await client.recordDecision(
          activeSessionId,
          msg.decision as string,
          msg.rationale as string,
          (msg.alternatives as string[]) || [],
          msg.confidence as number,
        );
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

function getNonce(): string {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "";
  for (let i = 0; i < 32; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}
