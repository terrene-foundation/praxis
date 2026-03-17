// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * TypeScript type definitions for Praxis API responses.
 *
 * These mirror the dict structures returned by the Python backend
 * (see src/praxis/api/handlers.py).
 */

/** JWT login response. */
export interface LoginResponse {
  access_token: string;
  token_type: string;
}

/** Session state as tracked by SessionManager. */
export type SessionState = "active" | "paused" | "ended";

/** A single constraint dimension within the envelope. */
export interface ConstraintDimension {
  limit: number;
  used: number;
  unit: string;
}

/** The five-dimension constraint envelope. */
export interface ConstraintEnvelope {
  financial: ConstraintDimension;
  operational: ConstraintDimension;
  temporal: ConstraintDimension;
  data_access: ConstraintDimension;
  communication: ConstraintDimension;
  [key: string]: ConstraintDimension;
}

/** A CO collaboration session. */
export interface Session {
  session_id: string;
  workspace_id: string;
  domain: string;
  state: SessionState;
  constraint_envelope: ConstraintEnvelope;
  created_at: string;
  ended_at?: string;
  summary?: string;
  genesis_id?: string;
  authority_id?: string;
}

/** List sessions response. */
export interface ListSessionsResponse {
  sessions: Session[];
}

/** Deliberation record from the timeline. */
export interface DeliberationRecord {
  record_id: string;
  record_type: string;
  content: string;
  actor: string;
  timestamp: string;
  reasoning_hash?: string;
  confidence?: number;
  alternatives?: string[];
}

/** Timeline response. */
export interface TimelineResponse {
  records: DeliberationRecord[];
  total: number;
}

/** Constraint gradient status for a single dimension. */
export interface GradientDimension {
  dimension: string;
  utilization: number;
  status: string;
}

/** Gradient response. */
export interface GradientResponse {
  dimensions: Record<string, GradientDimension> | GradientDimension[];
}

/** A held action awaiting human approval. */
export interface HeldAction {
  held_id: string;
  session_id: string;
  action: string;
  resource: string;
  dimension: string;
  reason: string;
  utilization: number;
  created_at: string;
}

/** List held actions response. */
export interface HeldActionsResponse {
  held_actions: HeldAction[];
  total: number;
}

/** Held action resolution result. */
export interface HeldActionResolution {
  held_id: string;
  resolution: string;
  resolved_by: string;
  resolved_at: string;
}

/** API error structure returned by handlers. */
export interface ApiError {
  error: {
    type: string;
    message: string;
  };
}

/** Health check response. */
export interface HealthResponse {
  status: string;
  version: string;
  domains: string[];
  db_status: string;
}
