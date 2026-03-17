// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Authentication store using Zustand.
 *
 * Manages JWT tokens, user identity, and role-based access.
 * Tokens are persisted to localStorage for session continuity.
 */

import { create } from "zustand";

import { praxisApi } from "@/services/api";
import type { LoginCredentials, User, UserRole } from "@/types/api";

// ---------------------------------------------------------------------------
// Store interface
// ---------------------------------------------------------------------------

interface AuthState {
  /** Current JWT token, or null if not authenticated */
  token: string | null;
  /** Current user profile, or null if not authenticated */
  user: User | null;
  /** Whether a login request is in progress */
  loading: boolean;
  /** Last authentication error message */
  error: string | null;
  /** Computed: whether the user is authenticated */
  isAuthenticated: boolean;
  /** Log in with credentials (legacy, kept for CLI and backward compat) */
  login: (credentials: LoginCredentials) => Promise<void>;
  /** Log in with a Firebase ID token (primary SSO path) */
  loginWithFirebase: (idToken: string) => Promise<void>;
  /** Log in with an OAuth token from URL fragment */
  loginWithToken: (token: string) => void;
  /** Log out and clear stored tokens */
  logout: () => void;
  /** Initialize auth state from stored token */
  initialize: () => void;
  /** Check if user has a specific role */
  hasRole: (role: UserRole) => boolean;
}

// ---------------------------------------------------------------------------
// Token persistence helpers
// ---------------------------------------------------------------------------

const TOKEN_KEY = "praxis_token";
const USER_KEY = "praxis_user";

function storeAuth(token: string, user: User): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Parse the 'sub' claim from a JWT token (without verification).
 * Used only to derive display info from an already-trusted token.
 */
function parseJwtSub(token: string): string {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.sub || "";
  } catch {
    return "";
  }
}

/**
 * Derive a User object from a JWT sub claim.
 * Handles both plain usernames and OAuth prefixed identities
 * (e.g., "github:octocat" or "google:user@gmail.com").
 */
function userFromSub(sub: string): User {
  let username = sub;
  if (sub.includes(":")) {
    // OAuth provider-prefixed identity
    username = sub.split(":").slice(1).join(":");
  }
  return {
    id: sub,
    username,
    role: "practitioner",
  };
}

function loadStoredAuth(): { token: string | null; user: User | null } {
  const token = localStorage.getItem(TOKEN_KEY);
  const userJson = localStorage.getItem(USER_KEY);
  let user: User | null = null;
  if (userJson) {
    try {
      user = JSON.parse(userJson) as User;
    } catch {
      // Invalid stored user — clear it
      localStorage.removeItem(USER_KEY);
    }
  }
  return { token, user };
}

// ---------------------------------------------------------------------------
// Store implementation
// ---------------------------------------------------------------------------

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  user: null,
  loading: false,
  error: null,
  isAuthenticated: false,

  login: async (credentials: LoginCredentials) => {
    set({ loading: true, error: null });
    try {
      const response = await praxisApi.auth.login(credentials);

      // The backend returns {access_token, token_type} without a user object.
      // Derive a local user from the credentials for the dashboard UI.
      const user: User = {
        id: credentials.username,
        username: credentials.username,
        role: "practitioner",
      };

      storeAuth(response.access_token, user);
      set({
        token: response.access_token,
        user,
        isAuthenticated: true,
        loading: false,
        error: null,
      });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Authentication failed";
      set({ loading: false, error: message });
      throw err;
    }
  },

  loginWithFirebase: async (idToken: string) => {
    set({ loading: true, error: null });
    try {
      const response = await praxisApi.auth.firebaseLogin(idToken);

      const user: User = {
        id: response.user.id,
        username: response.user.display_name || response.user.email,
        email: response.user.email,
        display_name: response.user.display_name,
        photo_url: response.user.photo_url ?? undefined,
        provider: response.user.provider,
        role: (response.user.role as User["role"]) || "practitioner",
      };

      storeAuth(response.access_token, user);
      set({
        token: response.access_token,
        user,
        isAuthenticated: true,
        loading: false,
        error: null,
      });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Authentication failed";
      set({ loading: false, error: message });
      throw err;
    }
  },

  loginWithToken: (token: string) => {
    const sub = parseJwtSub(token);
    const user = userFromSub(sub || "oauth-user");
    storeAuth(token, user);
    set({
      token,
      user,
      isAuthenticated: true,
      loading: false,
      error: null,
    });
  },

  logout: () => {
    clearAuth();
    set({
      token: null,
      user: null,
      isAuthenticated: false,
      error: null,
    });
  },

  initialize: () => {
    const { token, user } = loadStoredAuth();
    if (token && user) {
      set({
        token,
        user,
        isAuthenticated: true,
      });
    }
  },

  hasRole: (role: UserRole) => {
    const user = get().user;
    return user?.role === role;
  },
}));
