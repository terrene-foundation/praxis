// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Typed API client for the Praxis backend.
 *
 * All API URLs and secrets come from environment variables (VITE_ prefix).
 * The client handles JSON serialization, auth token injection, and error normalization.
 */

import type {
  AuditStatus,
  ChainStatus,
  ConstraintEnvelope,
  ConstraintUpdate,
  CreateSessionRequest,
  DecisionData,
  DelegationData,
  DelegationRecord,
  DeliberationRecord,
  FirebaseLoginResponse,
  GradientStatus,
  HeldActionList,
  HeldActionResolution,
  LoginCredentials,
  LoginResponse,
  ObservationData,
  Session,
  SessionList,
  SessionListParams,
  TimelineParams,
  TimelineResponse,
  VerificationBundle,
  VerificationResult,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const API_BASE = import.meta.env.VITE_PRAXIS_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------

class ApiClientError extends Error {
  status: number;
  body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.body = body;
  }
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("praxis_token");
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  options?: { responseType?: "blob" },
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const headers: Record<string, string> = {
    ...getAuthHeaders(),
  };

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let errorBody: unknown;
    try {
      errorBody = await response.json();
    } catch {
      errorBody = await response.text();
    }
    throw new ApiClientError(
      `API ${method} ${path} failed with status ${response.status}`,
      response.status,
      errorBody,
    );
  }

  if (options?.responseType === "blob") {
    return (await response.blob()) as T;
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

async function get<T>(
  path: string,
  params?: Record<string, string | number | boolean | undefined>,
): Promise<T> {
  let url = path;
  if (params) {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") {
        searchParams.set(key, String(value));
      }
    }
    const qs = searchParams.toString();
    if (qs) {
      url = `${path}?${qs}`;
    }
  }
  return request<T>("GET", url);
}

async function post<T>(
  path: string,
  body?: unknown,
  options?: { responseType?: "blob" },
): Promise<T> {
  return request<T>("POST", path, body, options);
}

async function put<T>(path: string, body?: unknown): Promise<T> {
  return request<T>("PUT", path, body);
}

// ---------------------------------------------------------------------------
// Typed API client
// ---------------------------------------------------------------------------

export const praxisApi = {
  // ---- Auth ----
  auth: {
    login: (credentials: LoginCredentials) =>
      post<LoginResponse>("/auth/login", credentials),

    /** Authenticate with a Firebase ID token (SSO via GitHub or Google) */
    firebaseLogin: (idToken: string) =>
      post<FirebaseLoginResponse>("/auth/firebase", { id_token: idToken }),

    /** Fetch which OAuth SSO providers are configured on the backend */
    providers: () => get<{ providers: string[] }>("/auth/providers"),
  },

  // ---- Sessions ----
  sessions: {
    create: (data: CreateSessionRequest) => post<Session>("/sessions", data),

    list: (params?: SessionListParams) =>
      get<SessionList>("/sessions", params as Record<string, string>),

    get: (id: string) => get<Session>(`/sessions/${id}`),

    pause: (id: string, reason?: string) =>
      post<Session>(`/sessions/${id}/pause`, { reason }),

    resume: (id: string) => post<Session>(`/sessions/${id}/resume`),

    end: (id: string, summary?: string) =>
      post<Session>(`/sessions/${id}/end`, { summary }),
  },

  // ---- Deliberation ----
  deliberation: {
    decide: (sessionId: string, data: DecisionData) =>
      post<DeliberationRecord>(`/sessions/${sessionId}/decide`, data),

    observe: (sessionId: string, data: ObservationData) =>
      post<DeliberationRecord>(`/sessions/${sessionId}/observe`, data),

    timeline: (sessionId: string, params?: TimelineParams) =>
      get<TimelineResponse>(
        `/sessions/${sessionId}/timeline`,
        params as Record<string, string | number>,
      ),
  },

  // ---- Constraints ----
  constraints: {
    get: (sessionId: string) =>
      get<{ constraint_envelope: ConstraintEnvelope }>(
        `/sessions/${sessionId}/constraints`,
      ),

    update: (sessionId: string, data: ConstraintUpdate) =>
      put<Session>(`/sessions/${sessionId}/constraints`, data),

    gradient: (sessionId: string) =>
      get<GradientStatus>(`/sessions/${sessionId}/gradient`),
  },

  // ---- Trust ----
  trust: {
    delegate: (sessionId: string, data: DelegationData) =>
      post<DelegationRecord>(`/sessions/${sessionId}/delegate`, data),

    approve: (sessionId: string, heldId: string) =>
      post<HeldActionResolution>(`/sessions/${sessionId}/approve/${heldId}`),

    deny: (sessionId: string, heldId: string) =>
      post<HeldActionResolution>(`/sessions/${sessionId}/deny/${heldId}`),

    heldActions: (sessionId: string) =>
      get<HeldActionList>(`/sessions/${sessionId}/held-actions`),

    chain: (sessionId: string) =>
      get<ChainStatus>(`/sessions/${sessionId}/chain`),
  },

  // ---- Verification ----
  verification: {
    verify: (sessionId: string) =>
      post<VerificationResult>(`/sessions/${sessionId}/verify`),

    export: (sessionId: string) =>
      post<VerificationBundle>(`/sessions/${sessionId}/export`, {}),

    audit: (sessionId: string) =>
      get<AuditStatus>(`/sessions/${sessionId}/audit`),
  },
};

export { ApiClientError };
