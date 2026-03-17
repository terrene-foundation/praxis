// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Main entry point for the Praxis VS Code extension.
 *
 * Activates on startup (onStartupFinished) and registers:
 *   - PraxisClient           (API communication)
 *   - SidebarProvider         (webview sidebar for session management)
 *   - PraxisStatusBar         (status bar constraint indicator)
 *   - ApprovalNotifier        (held action notifications)
 *   - Commands                (configure, startSession, endSession, recordDecision, MCP)
 */

import * as vscode from "vscode";
import { PraxisClient } from "./api/client";
import { showMcpSetup, writeMcpConfig } from "./mcp/McpConfigWriter";
import { ApprovalNotifier } from "./views/ApprovalNotifier";
import { showDecisionForm } from "./views/DecisionForm";
import { SidebarProvider } from "./views/SidebarProvider";
import { PraxisStatusBar } from "./views/StatusBarItem";

export function activate(context: vscode.ExtensionContext): void {
  // -- API Client --
  const client = new PraxisClient(context.secrets);

  // -- Sidebar --
  const sidebarProvider = new SidebarProvider(context.extensionUri, client);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      SidebarProvider.viewType,
      sidebarProvider,
    ),
  );

  // -- Status Bar --
  const statusBar = new PraxisStatusBar(client);
  statusBar.startPolling();
  context.subscriptions.push({ dispose: () => statusBar.dispose() });

  // -- Approval Notifier --
  const notifier = new ApprovalNotifier(client, context.extensionUri);
  notifier.startPolling();
  context.subscriptions.push({ dispose: () => notifier.dispose() });

  // -- Commands --

  context.subscriptions.push(
    vscode.commands.registerCommand("praxis.configure", async () => {
      const url = await vscode.window.showInputBox({
        prompt: "Praxis server URL",
        value:
          vscode.workspace
            .getConfiguration("praxis")
            .get<string>("serverUrl") ?? "http://localhost:8000",
        validateInput: (val) => {
          try {
            new URL(val);
            return null;
          } catch {
            return "Enter a valid URL (e.g. http://localhost:8000)";
          }
        },
      });
      if (url) {
        await vscode.workspace
          .getConfiguration("praxis")
          .update("serverUrl", url, vscode.ConfigurationTarget.Global);
        vscode.window.showInformationMessage(`Praxis server URL set to ${url}`);
        // Trigger a refresh so the sidebar and status bar pick up the new URL
        sidebarProvider.refresh();
      }
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("praxis.startSession", async () => {
      const workspace = await vscode.window.showInputBox({
        prompt: "Workspace ID",
        value: "default",
      });
      if (!workspace) {
        return;
      }

      const domain = await vscode.window.showQuickPick(
        [
          { label: "COC", description: "Codegen", value: "coc" },
          { label: "COE", description: "Education", value: "coe" },
          { label: "COG", description: "Governance", value: "cog" },
        ],
        { placeHolder: "Select CO domain" },
      );
      if (!domain) {
        return;
      }

      try {
        const session = await client.createSession(workspace, domain.value);
        vscode.window.showInformationMessage(
          `Session started: ${session.session_id.slice(0, 8)}`,
        );
        sidebarProvider.refresh();
      } catch (err) {
        vscode.window.showErrorMessage(
          `Failed to start session: ${err instanceof Error ? err.message : String(err)}`,
        );
      }
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("praxis.endSession", async () => {
      try {
        const listRes = await client.listSessions();
        const active = listRes.sessions.filter((s) => s.state === "active");
        if (active.length === 0) {
          vscode.window.showInformationMessage("No active sessions.");
          return;
        }

        const picked = await vscode.window.showQuickPick(
          active.map((s) => ({
            label: s.session_id.slice(0, 8),
            description: `${s.domain} | ${s.workspace_id}`,
            sessionId: s.session_id,
          })),
          { placeHolder: "Select session to end" },
        );
        if (!picked) {
          return;
        }

        const summary = await vscode.window.showInputBox({
          prompt: "Session summary (optional)",
        });

        await client.endSession(picked.sessionId, summary ?? "");
        vscode.window.showInformationMessage(`Session ended: ${picked.label}`);
        sidebarProvider.refresh();
      } catch (err) {
        vscode.window.showErrorMessage(
          `Failed to end session: ${err instanceof Error ? err.message : String(err)}`,
        );
      }
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("praxis.recordDecision", () => {
      showDecisionForm(client, context.extensionUri);
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("praxis.configureMcp", () => {
      writeMcpConfig();
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("praxis.mcpSetup", () => {
      showMcpSetup(context.extensionUri, client);
    }),
  );
}

export function deactivate(): void {
  // Cleanup handled by disposables registered in activate()
}
