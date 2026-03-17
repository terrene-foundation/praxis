// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * TanStack Query hooks for the Praxis API.
 *
 * Each hook wraps a single API call with proper query keys, caching,
 * and error handling. Mutations invalidate relevant queries automatically.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { praxisApi } from "@/services/api";
import type {
  CreateSessionRequest,
  DecisionData,
  DelegationData,
  ObservationData,
  SessionListParams,
  TimelineParams,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Query keys factory
// ---------------------------------------------------------------------------

export const queryKeys = {
  sessions: {
    all: ["sessions"] as const,
    list: (params?: SessionListParams) => ["sessions", "list", params] as const,
    detail: (id: string) => ["sessions", "detail", id] as const,
  },
  deliberation: {
    timeline: (sessionId: string, params?: TimelineParams) =>
      ["deliberation", "timeline", sessionId, params] as const,
  },
  constraints: {
    detail: (sessionId: string) => ["constraints", sessionId] as const,
    gradient: (sessionId: string) =>
      ["constraints", "gradient", sessionId] as const,
  },
  trust: {
    chain: (sessionId: string) => ["trust", "chain", sessionId] as const,
    heldActions: (sessionId: string) =>
      ["trust", "heldActions", sessionId] as const,
  },
  verification: {
    audit: (sessionId: string) => ["verification", "audit", sessionId] as const,
  },
} as const;

// ---------------------------------------------------------------------------
// Session queries
// ---------------------------------------------------------------------------

export function useSessions(params?: SessionListParams) {
  return useQuery({
    queryKey: queryKeys.sessions.list(params),
    queryFn: () => praxisApi.sessions.list(params),
  });
}

export function useSession(id: string) {
  return useQuery({
    queryKey: queryKeys.sessions.detail(id),
    queryFn: () => praxisApi.sessions.get(id),
    enabled: !!id,
  });
}

// ---------------------------------------------------------------------------
// Session mutations
// ---------------------------------------------------------------------------

export function useCreateSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateSessionRequest) => praxisApi.sessions.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.sessions.all,
      });
    },
  });
}

export function usePauseSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      praxisApi.sessions.pause(id, reason),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.sessions.detail(variables.id),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.sessions.all,
      });
    },
  });
}

export function useResumeSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => praxisApi.sessions.resume(id),
    onSuccess: (_data, id) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.sessions.detail(id),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.sessions.all,
      });
    },
  });
}

export function useEndSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, summary }: { id: string; summary?: string }) =>
      praxisApi.sessions.end(id, summary),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.sessions.detail(variables.id),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.sessions.all,
      });
    },
  });
}

// ---------------------------------------------------------------------------
// Deliberation queries and mutations
// ---------------------------------------------------------------------------

export function useTimeline(sessionId: string, params?: TimelineParams) {
  return useQuery({
    queryKey: queryKeys.deliberation.timeline(sessionId, params),
    queryFn: () => praxisApi.deliberation.timeline(sessionId, params),
    enabled: !!sessionId,
  });
}

export function useDecide() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      data,
    }: {
      sessionId: string;
      data: DecisionData;
    }) => praxisApi.deliberation.decide(sessionId, data),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: ["deliberation", "timeline", variables.sessionId],
      });
    },
  });
}

export function useObserve() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      data,
    }: {
      sessionId: string;
      data: ObservationData;
    }) => praxisApi.deliberation.observe(sessionId, data),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: ["deliberation", "timeline", variables.sessionId],
      });
    },
  });
}

// ---------------------------------------------------------------------------
// Constraint queries
// ---------------------------------------------------------------------------

export function useConstraints(sessionId: string) {
  return useQuery({
    queryKey: queryKeys.constraints.detail(sessionId),
    queryFn: () => praxisApi.constraints.get(sessionId),
    enabled: !!sessionId,
  });
}

export function useGradient(sessionId: string) {
  return useQuery({
    queryKey: queryKeys.constraints.gradient(sessionId),
    queryFn: () => praxisApi.constraints.gradient(sessionId),
    enabled: !!sessionId,
  });
}

// ---------------------------------------------------------------------------
// Trust queries and mutations
// ---------------------------------------------------------------------------

export function useTrustChain(sessionId: string) {
  return useQuery({
    queryKey: queryKeys.trust.chain(sessionId),
    queryFn: () => praxisApi.trust.chain(sessionId),
    enabled: !!sessionId,
  });
}

export function useHeldActions(sessionId: string) {
  return useQuery({
    queryKey: queryKeys.trust.heldActions(sessionId),
    queryFn: () => praxisApi.trust.heldActions(sessionId),
    enabled: !!sessionId,
  });
}

export function useDelegate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      data,
    }: {
      sessionId: string;
      data: DelegationData;
    }) => praxisApi.trust.delegate(sessionId, data),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.trust.chain(variables.sessionId),
      });
    },
  });
}

export function useApproveAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      heldId,
    }: {
      sessionId: string;
      heldId: string;
    }) => praxisApi.trust.approve(sessionId, heldId),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.sessions.detail(variables.sessionId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.trust.heldActions(variables.sessionId),
      });
    },
  });
}

export function useDenyAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      heldId,
    }: {
      sessionId: string;
      heldId: string;
    }) => praxisApi.trust.deny(sessionId, heldId),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.sessions.detail(variables.sessionId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.trust.heldActions(variables.sessionId),
      });
    },
  });
}

// ---------------------------------------------------------------------------
// Verification queries
// ---------------------------------------------------------------------------

export function useAudit(sessionId: string) {
  return useQuery({
    queryKey: queryKeys.verification.audit(sessionId),
    queryFn: () => praxisApi.verification.audit(sessionId),
    enabled: !!sessionId,
  });
}

export function useVerify() {
  return useMutation({
    mutationFn: (sessionId: string) => praxisApi.verification.verify(sessionId),
  });
}

export function useExportBundle() {
  return useMutation({
    mutationFn: (sessionId: string) => praxisApi.verification.export(sessionId),
  });
}
