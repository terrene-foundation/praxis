// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * HTTP client for the Praxis REST API.
 *
 * Handles authentication, request construction, and response parsing.
 * Server URL comes from VS Code settings; JWT token is stored in
 * SecretStorage so it never touches globalState or disk.
 */

import * as vscode from "vscode";
import type {
  ApiError,
  GradientResponse,
  HealthResponse,
  HeldActionResolution,
  HeldActionsResponse,
  ListSessionsResponse,
  LoginResponse,
  Session,
  TimelineResponse,
} from "./types";

const TOKEN_KEY = "praxis.jwt";

/**
 * Determine whether an API response is an error envelope.
 */
function isApiError(body: unknown): body is ApiError {
  return (
    typeof body === "object" &&
    body !== null &&
    "error" in body &&
    typeof (body as ApiError).error === "object"
  );
}

/**
 * Thin HTTP client that talks to the Praxis backend over REST.
 *
 * Usage:
 *   const client = new PraxisClient(context.secrets);
 *   await client.login("admin", "admin");
 *   const sessions = await client.listSessions();
 */
export class PraxisClient {
  private secrets: vscode.SecretStorage;

  constructor(secrets: vscode.SecretStorage) {
    this.secrets = secrets;
  }

  // -------------------------------------------------------------------
  // Configuration helpers
  // -------------------------------------------------------------------

  /** Read the server base URL from VS Code settings. */
  private getBaseUrl(): string {
    const cfg = vscode.workspace.getConfiguration("praxis");
    return cfg.get<string>("serverUrl") ?? "http://localhost:8000";
  }

  /** Retrieve the stored JWT token (or undefined). */
  async getToken(): Promise<string | undefined> {
    return this.secrets.get(TOKEN_KEY);
  }

  /** Persist a JWT token into SecretStorage. */
  async setToken(token: string): Promise<void> {
    await this.secrets.store(TOKEN_KEY, token);
  }

  /** Clear the stored JWT token (logout). */
  async clearToken(): Promise<void> {
    await this.secrets.delete(TOKEN_KEY);
  }

  // -------------------------------------------------------------------
  // Low-level HTTP
  // -------------------------------------------------------------------

  /**
   * Send an HTTP request to the Praxis server.
   *
   * Automatically attaches the Authorization header when a token is
   * available. Returns the parsed JSON body or throws on network /
   * HTTP errors.
   */
  private async request<T>(
    method: string,
    path: string,
    body?: Record<string, unknown>,
  ): Promise<T> {
    const url = `${this.getBaseUrl()}${path}`;
    const token = await this.getToken();

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const init: RequestInit = { method, headers };
    if (body !== undefined) {
      init.body = JSON.stringify(body);
    }

    const response = await fetch(url, init);
    const json = (await response.json()) as T;

    if (isApiError(json)) {
      throw new Error(`Praxis API error: ${(json as ApiError).error.message}`);
    }

    return json;
  }

  private get<T>(path: string): Promise<T> {
    return this.request<T>("GET", path);
  }

  private post<T>(path: string, body?: Record<string, unknown>): Promise<T> {
    return this.request<T>("POST", path, body ?? {});
  }

  // -------------------------------------------------------------------
  // Auth
  // -------------------------------------------------------------------

  /** Authenticate and persist the JWT token. */
  async login(username: string, password: string): Promise<LoginResponse> {
    const res = await this.post<LoginResponse>("/auth/login", {
      username,
      password,
    });
    await this.setToken(res.access_token);
    return res;
  }

  // -------------------------------------------------------------------
  // Sessions
  // -------------------------------------------------------------------

  /** Create a new CO collaboration session. */
  async createSession(
    workspaceId: string,
    domain: string = "coc",
    constraintTemplate: string = "moderate",
  ): Promise<Session> {
    return this.post<Session>("/sessions", {
      workspace_id: workspaceId,
      domain,
      constraint_template: constraintTemplate,
    });
  }

  /** List sessions, optionally filtered. */
  async listSessions(
    workspaceId?: string,
    state?: string,
  ): Promise<ListSessionsResponse> {
    const params = new URLSearchParams();
    if (workspaceId) {
      params.set("workspace_id", workspaceId);
    }
    if (state) {
      params.set("state", state);
    }
    const qs = params.toString();
    const path = qs ? `/sessions?${qs}` : "/sessions";
    return this.get<ListSessionsResponse>(path);
  }

  /** Get a single session by ID. */
  async getSession(id: string): Promise<Session> {
    return this.get<Session>(`/sessions/${encodeURIComponent(id)}`);
  }

  /** Pause an active session. */
  async pauseSession(id: string, reason?: string): Promise<Session> {
    return this.post<Session>(
      `/sessions/${encodeURIComponent(id)}/pause`,
      reason ? { reason } : {},
    );
  }

  /** Resume a paused session. */
  async resumeSession(id: string): Promise<Session> {
    return this.post<Session>(`/sessions/${encodeURIComponent(id)}/resume`);
  }

  /** End (archive) a session. */
  async endSession(id: string, summary?: string): Promise<Session> {
    return this.post<Session>(
      `/sessions/${encodeURIComponent(id)}/end`,
      summary ? { summary } : {},
    );
  }

  // -------------------------------------------------------------------
  // Deliberation
  // -------------------------------------------------------------------

  /** Record a human decision in a session. */
  async recordDecision(
    sessionId: string,
    decision: string,
    rationale: string,
    alternatives?: string[],
    confidence?: number,
  ): Promise<Record<string, unknown>> {
    const body: Record<string, unknown> = {
      decision,
      rationale,
      actor: "human",
    };
    if (alternatives && alternatives.length > 0) {
      body.alternatives = alternatives;
    }
    if (confidence !== undefined) {
      body.confidence = confidence / 100; // UI sends 0-100, API expects 0-1
    }
    return this.post<Record<string, unknown>>(
      `/sessions/${encodeURIComponent(sessionId)}/decide`,
      body,
    );
  }

  /** Get the deliberation timeline for a session. */
  async getTimeline(sessionId: string): Promise<TimelineResponse> {
    return this.get<TimelineResponse>(
      `/sessions/${encodeURIComponent(sessionId)}/timeline`,
    );
  }

  // -------------------------------------------------------------------
  // Constraints
  // -------------------------------------------------------------------

  /** Get the constraint envelope for a session. */
  async getConstraints(sessionId: string): Promise<Record<string, unknown>> {
    return this.get<Record<string, unknown>>(
      `/sessions/${encodeURIComponent(sessionId)}/constraints`,
    );
  }

  /** Get the constraint gradient (utilization per dimension). */
  async getGradient(sessionId: string): Promise<GradientResponse> {
    return this.get<GradientResponse>(
      `/sessions/${encodeURIComponent(sessionId)}/gradient`,
    );
  }

  // -------------------------------------------------------------------
  // Held actions
  // -------------------------------------------------------------------

  /** List pending held actions for a session. */
  async getHeldActions(sessionId: string): Promise<HeldActionsResponse> {
    return this.get<HeldActionsResponse>(
      `/sessions/${encodeURIComponent(sessionId)}/held-actions`,
    );
  }

  /** Approve a held action. */
  async approveAction(
    sessionId: string,
    heldId: string,
  ): Promise<HeldActionResolution> {
    return this.post<HeldActionResolution>(
      `/sessions/${encodeURIComponent(sessionId)}/approve/${encodeURIComponent(heldId)}`,
    );
  }

  /** Deny a held action. */
  async denyAction(
    sessionId: string,
    heldId: string,
  ): Promise<HeldActionResolution> {
    return this.post<HeldActionResolution>(
      `/sessions/${encodeURIComponent(sessionId)}/deny/${encodeURIComponent(heldId)}`,
    );
  }

  // -------------------------------------------------------------------
  // Health
  // -------------------------------------------------------------------

  /** Check server health — useful for connectivity test. */
  async health(): Promise<HealthResponse> {
    return this.get<HealthResponse>("/health");
  }
}
