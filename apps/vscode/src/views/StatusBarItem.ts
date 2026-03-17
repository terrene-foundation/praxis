// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Status bar item that shows Praxis trust state at a glance.
 *
 * Displays constraint utilization, held action count, or offline
 * status. Clicking it reveals the Praxis sidebar.
 */

import * as vscode from "vscode";
import { PraxisClient } from "../api/client";
import type { GradientDimension, Session } from "../api/types";

export class PraxisStatusBar {
  private item: vscode.StatusBarItem;
  private client: PraxisClient;
  private pollTimer?: ReturnType<typeof setInterval>;

  constructor(client: PraxisClient) {
    this.client = client;
    this.item = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Left,
      100,
    );
    this.item.command = "praxis.sessionView.focus";
    this.item.tooltip = "Praxis — Trust-Aware AI Collaboration";
    this.setOffline();
    this.item.show();
  }

  /** Start periodic status updates. */
  startPolling(): void {
    const cfg = vscode.workspace.getConfiguration("praxis");
    const seconds = cfg.get<number>("pollIntervalSeconds") ?? 30;
    this.pollTimer = setInterval(() => this.refresh(), seconds * 1000);
    // Immediate first update
    this.refresh();
  }

  /** Stop periodic updates. */
  stopPolling(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = undefined;
    }
  }

  /** Dispose of the status bar item. */
  dispose(): void {
    this.stopPolling();
    this.item.dispose();
  }

  // -------------------------------------------------------------------
  // Refresh logic
  // -------------------------------------------------------------------

  private async refresh(): Promise<void> {
    try {
      // Quick connectivity check via list sessions
      const listRes = await this.client.listSessions();
      const active: Session | undefined = listRes.sessions.find(
        (s) => s.state === "active",
      );

      if (!active) {
        this.setIdle();
        return;
      }

      // Check held actions first — they take priority
      try {
        const heldRes = await this.client.getHeldActions(active.session_id);
        if (heldRes.total > 0) {
          this.setHeld(heldRes.total);
          return;
        }
      } catch {
        // Held actions endpoint may not be configured; continue
      }

      // Check constraint gradient
      try {
        const gradientRes = await this.client.getGradient(active.session_id);
        const dims = normalizeGradient(gradientRes.dimensions);
        const worst = dims.reduce<GradientDimension | null>((prev, d) => {
          if (!prev || d.utilization > prev.utilization) {
            return d;
          }
          return prev;
        }, null);

        if (worst && worst.utilization > 0.7) {
          this.setWarning(worst.dimension, Math.round(worst.utilization * 100));
          return;
        }
      } catch {
        // Gradient endpoint may fail; fall through to OK
      }

      this.setOk();
    } catch {
      this.setOffline();
    }
  }

  // -------------------------------------------------------------------
  // Display states
  // -------------------------------------------------------------------

  private setOk(): void {
    this.item.text = "$(shield) Praxis: OK";
    this.item.backgroundColor = undefined;
  }

  private setIdle(): void {
    this.item.text = "$(shield) Praxis: No session";
    this.item.backgroundColor = undefined;
  }

  private setWarning(dimension: string, pct: number): void {
    const label = capitalise(dimension);
    this.item.text = `$(shield) Praxis: ${label} ${pct}%`;
    this.item.backgroundColor = new vscode.ThemeColor(
      "statusBarItem.warningBackground",
    );
  }

  private setHeld(count: number): void {
    this.item.text = `$(shield) Praxis: HELD (${count})`;
    this.item.backgroundColor = new vscode.ThemeColor(
      "statusBarItem.warningBackground",
    );
  }

  private setOffline(): void {
    this.item.text = "$(shield) Praxis: offline";
    this.item.backgroundColor = new vscode.ThemeColor(
      "statusBarItem.errorBackground",
    );
  }
}

// -------------------------------------------------------------------
// Helpers
// -------------------------------------------------------------------

function capitalise(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

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
