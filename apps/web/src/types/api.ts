// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * TypeScript types matching the Praxis backend API.
 *
 * These types mirror the Python data structures from praxis.core and praxis.api
 * to ensure type-safe communication between the web dashboard and the API server.
 */

// ---------------------------------------------------------------------------
// Session types
// ---------------------------------------------------------------------------

export type SessionState = "creating" | "active" | "paused" | "archived";

export interface Session {
  session_id: string;
  workspace_id: string;
  domain: string;
  state: SessionState;
  constraint_envelope: ConstraintEnvelope;
  genesis_id: string | null;
  genesis_chain_entry: Record<string, unknown> | null;
  current_phase: string | null;
  phase_list: string[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  ended_at: string | null;
}

export interface CreateSessionRequest {
  workspace_id: string;
  domain?: string;
  constraint_template?: string;
  constraints?: ConstraintEnvelope;
  authority_id?: string;
}

export interface SessionListParams {
  workspace_id?: string;
  state?: SessionState;
}

export interface SessionList {
  sessions: Session[];
}

// ---------------------------------------------------------------------------
// Constraint types
// ---------------------------------------------------------------------------

export interface FinancialConstraint {
  max_spend: number;
  current_spend: number;
}

export interface OperationalConstraint {
  allowed_actions: string[];
  blocked_actions: string[];
}

export interface TemporalConstraint {
  max_duration_minutes: number;
  elapsed_minutes: number;
}

export interface DataAccessConstraint {
  allowed_paths: string[];
  blocked_paths: string[];
}

export interface CommunicationConstraint {
  allowed_channels: string[];
  blocked_channels: string[];
}

export interface ConstraintEnvelope {
  financial: FinancialConstraint;
  operational: OperationalConstraint;
  temporal: TemporalConstraint;
  data_access: DataAccessConstraint;
  communication: CommunicationConstraint;
}

export interface ConstraintUpdate {
  financial?: Partial<FinancialConstraint>;
  operational?: Partial<OperationalConstraint>;
  temporal?: Partial<TemporalConstraint>;
  data_access?: Partial<DataAccessConstraint>;
  communication?: Partial<CommunicationConstraint>;
}

export type GradientLevel = "auto_approved" | "flagged" | "held" | "blocked";

export interface DimensionStatus {
  dimension: string;
  level: GradientLevel;
  utilization: number;
  reason: string;
}

export interface GradientStatus {
  dimensions: DimensionStatus[];
}

// ---------------------------------------------------------------------------
// Deliberation types
// ---------------------------------------------------------------------------

export type RecordType = "decision" | "observation" | "escalation";

export interface DeliberationRecord {
  record_id: string;
  session_id: string;
  record_type: RecordType;
  content: Record<string, unknown>;
  reasoning_trace: Record<string, unknown>;
  reasoning_hash: string;
  parent_record_id: string | null;
  anchor_id: string | null;
  actor: string;
  confidence: number | null;
  created_at: string;
}

export interface DecisionData {
  decision: string;
  rationale: string;
  actor?: string;
  alternatives?: string[];
  confidence?: number;
}

export interface ObservationData {
  observation: string;
  actor?: string;
  confidence?: number;
}

export interface TimelineParams {
  record_type?: RecordType;
  limit?: number;
  offset?: number;
}

export interface TimelineResponse {
  records: DeliberationRecord[];
  total: number;
}

// ---------------------------------------------------------------------------
// Trust types
// ---------------------------------------------------------------------------

export interface DelegationData {
  delegate_id: string;
}

export interface DelegationRecord {
  delegation_id: string;
  session_id: string;
  delegate_id: string;
  constraints: ConstraintEnvelope;
  content_hash: string;
  parent_hash: string;
  created_at: string;
}

export interface HeldAction {
  held_id: string;
  session_id: string;
  action: string;
  resource: string;
  dimension: string;
  reason: string;
  utilization: number;
  resolution?: "approved" | "denied";
  resolved_by?: string;
  resolved_at?: string;
  created_at: string;
}

export interface HeldActionList {
  held_actions: HeldAction[];
  total: number;
}

export interface HeldActionResolution {
  held_id: string;
  resolution: "approved" | "denied";
  resolved_by: string;
  resolved_at: string;
}

export interface ChainStatus {
  chain_length: number;
  head_hash: string;
  valid: boolean;
  breaks: string[];
}

// ---------------------------------------------------------------------------
// Verification types
// ---------------------------------------------------------------------------

export interface VerificationResult {
  valid: boolean;
  total_entries: number;
  verified_entries: number;
  breaks: string[];
}

export interface VerificationBundle {
  session_id: string;
  entries: ChainEntry[];
  public_keys: Record<string, string>;
  chain_length: number;
}

export interface ChainEntry {
  payload: Record<string, unknown>;
  content_hash: string;
  signature: string;
  signer_key_id: string;
  parent_hash: string;
}

export interface AuditStatus {
  chain_length: number;
  valid: boolean;
  breaks: string[];
}

// ---------------------------------------------------------------------------
// Auth types
// ---------------------------------------------------------------------------

export interface User {
  id: string;
  username: string;
  email?: string;
  display_name?: string;
  photo_url?: string;
  provider?: string;
  role: UserRole;
}

export type UserRole = "practitioner" | "supervisor" | "auditor" | "admin";

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface FirebaseLoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    display_name: string;
    photo_url: string | null;
    provider: string;
    role: string;
  };
}

// ---------------------------------------------------------------------------
// WebSocket event types
// ---------------------------------------------------------------------------

export type PraxisEventType =
  | "session_state_changed"
  | "constraint_updated"
  | "held_action_created"
  | "held_action_resolved"
  | "deliberation_recorded";

export interface PraxisEvent {
  type: PraxisEventType;
  data: Record<string, unknown>;
  timestamp: string;
}

// ---------------------------------------------------------------------------
// API error type
// ---------------------------------------------------------------------------

export interface ApiError {
  error: string;
  error_code: string;
  detail?: string;
}
