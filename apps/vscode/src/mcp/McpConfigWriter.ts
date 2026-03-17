// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * MCP configuration writer and setup walkthrough.
 *
 * Provides two commands:
 *   - praxis.configureMcp  — writes MCP server config to .vscode/mcp.json
 *   - praxis.mcpSetup      — opens a walkthrough webview explaining first-time setup
 *
 * Also exposes a helper to check MCP connection status for display
 * in the sidebar.
 */

import * as vscode from "vscode";
import { PraxisClient } from "../api/client";

/** The MCP server configuration that Praxis generates. */
const MCP_CONFIG = {
  mcpServers: {
    praxis: {
      command: "praxis",
      args: ["mcp", "serve"],
    },
  },
};

/**
 * Write `.vscode/mcp.json` into the current workspace root.
 *
 * If no workspace is open, prompts the user to open a folder first.
 * If the file already exists, asks for confirmation before overwriting.
 */
export async function writeMcpConfig(): Promise<void> {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders || folders.length === 0) {
    vscode.window.showErrorMessage(
      "Open a workspace folder before configuring MCP.",
    );
    return;
  }

  const root = folders[0].uri;
  const vscodeDir = vscode.Uri.joinPath(root, ".vscode");
  const mcpFile = vscode.Uri.joinPath(vscodeDir, "mcp.json");

  // Check if file already exists
  try {
    await vscode.workspace.fs.stat(mcpFile);
    const overwrite = await vscode.window.showWarningMessage(
      ".vscode/mcp.json already exists. Overwrite?",
      "Overwrite",
      "Cancel",
    );
    if (overwrite !== "Overwrite") {
      return;
    }
  } catch {
    // File does not exist — good, create it
  }

  // Ensure .vscode/ directory exists
  try {
    await vscode.workspace.fs.createDirectory(vscodeDir);
  } catch {
    // Directory may already exist
  }

  const content = JSON.stringify(MCP_CONFIG, null, 2) + "\n";
  await vscode.workspace.fs.writeFile(mcpFile, Buffer.from(content, "utf-8"));

  vscode.window.showInformationMessage(
    "Praxis MCP configuration written to .vscode/mcp.json",
  );

  // Open the file for the user to review
  const doc = await vscode.workspace.openTextDocument(mcpFile);
  await vscode.window.showTextDocument(doc);
}

/**
 * Show the MCP setup walkthrough as a webview panel.
 *
 * Guides the user through installing the Praxis CLI, configuring
 * MCP, and verifying the connection.
 */
export function showMcpSetup(
  extensionUri: vscode.Uri,
  client: PraxisClient,
): void {
  const panel = vscode.window.createWebviewPanel(
    "praxis.mcpSetup",
    "Praxis MCP Setup",
    vscode.ViewColumn.One,
    {
      enableScripts: true,
      localResourceRoots: [extensionUri],
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
      padding: 24px;
      max-width: 700px;
      margin: 0 auto;
      line-height: 1.5;
    }
    h1 { margin-top: 0; }
    h2 { margin-top: 24px; font-size: 16px; }
    code {
      background: var(--vscode-textCodeBlock-background);
      padding: 2px 6px;
      border-radius: 3px;
      font-family: var(--vscode-editor-font-family);
      font-size: 13px;
    }
    pre {
      background: var(--vscode-textCodeBlock-background);
      padding: 12px;
      border-radius: 4px;
      overflow-x: auto;
      font-family: var(--vscode-editor-font-family);
      font-size: 13px;
      line-height: 1.4;
    }
    .step {
      display: flex;
      gap: 12px;
      margin: 16px 0;
      padding: 12px;
      border: 1px solid var(--vscode-widget-border);
      border-radius: 4px;
    }
    .step-number {
      flex-shrink: 0;
      width: 28px; height: 28px;
      border-radius: 50%;
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      display: flex; align-items: center; justify-content: center;
      font-weight: bold; font-size: 14px;
    }
    .step-content { flex: 1; }
    button {
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none; padding: 8px 16px; cursor: pointer;
      border-radius: 2px; font-size: 13px; margin-top: 8px;
    }
    button:hover { background: var(--vscode-button-hoverBackground); }
    .status { margin-top: 16px; padding: 12px; border-radius: 4px; font-size: 13px; }
    .status.ok { background: var(--vscode-testing-iconPassed); color: #fff; }
    .status.fail { background: var(--vscode-editorError-foreground); color: #fff; }
    .status.checking { background: var(--vscode-editorWarning-foreground); color: #fff; }
  </style>
</head>
<body>
  <h1>Praxis MCP Setup</h1>
  <p>
    The Model Context Protocol (MCP) allows AI assistants in your IDE to
    communicate directly with the Praxis runtime. Follow these steps to
    set up the connection.
  </p>

  <div class="step">
    <div class="step-number">1</div>
    <div class="step-content">
      <strong>Install the Praxis CLI</strong>
      <p>The Praxis CLI includes the MCP server. Install it with pip:</p>
      <pre>pip install praxis-co</pre>
      <p>Verify installation:</p>
      <pre>praxis --version</pre>
    </div>
  </div>

  <div class="step">
    <div class="step-number">2</div>
    <div class="step-content">
      <strong>Start the Praxis server</strong>
      <p>The MCP server needs the Praxis backend running:</p>
      <pre>praxis serve</pre>
      <p>By default this starts on <code>http://localhost:8000</code>.</p>
    </div>
  </div>

  <div class="step">
    <div class="step-number">3</div>
    <div class="step-content">
      <strong>Generate MCP configuration</strong>
      <p>Click the button below to create <code>.vscode/mcp.json</code>:</p>
      <button onclick="vscode.postMessage({command:'writeMcpConfig'})">Generate MCP Config</button>
      <p>Or run the command palette: <code>Praxis: Configure MCP Server</code></p>
    </div>
  </div>

  <div class="step">
    <div class="step-number">4</div>
    <div class="step-content">
      <strong>Verify connection</strong>
      <p>Click below to test the connection to the Praxis server:</p>
      <button onclick="vscode.postMessage({command:'checkHealth'})">Check Connection</button>
      <div id="status"></div>
    </div>
  </div>

  <h2>MCP Configuration Reference</h2>
  <p>The generated <code>.vscode/mcp.json</code> looks like this:</p>
  <pre>${escapeHtml(JSON.stringify(MCP_CONFIG, null, 2))}</pre>
  <p>
    This tells VS Code (and MCP-compatible AI assistants) to launch
    <code>praxis mcp serve</code> as the MCP server process. The Praxis
    MCP server exposes session management, deliberation capture, and
    constraint enforcement as MCP tools.
  </p>

  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    window.addEventListener('message', function(event) {
      const msg = event.data;
      if (msg.command === 'healthResult') {
        const el = document.getElementById('status');
        if (!el) return;
        if (msg.success) {
          el.className = 'status ok';
          el.textContent = 'Connected to Praxis ' + msg.version + ' (status: ' + msg.dbStatus + ')';
        } else {
          el.className = 'status fail';
          el.textContent = 'Connection failed: ' + msg.error;
        }
      }
    });
  </script>
</body>
</html>`;

  panel.webview.onDidReceiveMessage(async (msg) => {
    if (msg.command === "writeMcpConfig") {
      await writeMcpConfig();
    } else if (msg.command === "checkHealth") {
      try {
        const health = await client.health();
        panel.webview.postMessage({
          command: "healthResult",
          success: true,
          version: health.version,
          dbStatus: health.db_status,
        });
      } catch (err) {
        panel.webview.postMessage({
          command: "healthResult",
          success: false,
          error: err instanceof Error ? err.message : String(err),
        });
      }
    }
  });
}

/**
 * Check whether the Praxis MCP server is reachable.
 *
 * Returns a status string for display in the sidebar.
 */
export async function getMcpStatus(client: PraxisClient): Promise<string> {
  try {
    const health = await client.health();
    return `MCP: connected (v${health.version})`;
  } catch {
    return "MCP: not connected";
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
