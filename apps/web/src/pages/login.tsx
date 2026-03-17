// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { signInWithPopup } from "firebase/auth";
import { Network, AlertCircle, Loader2, Github } from "lucide-react";

import { auth, githubProvider, googleProvider } from "@/lib/firebase";
import { useAuthStore } from "@/stores/auth";

// ---------------------------------------------------------------------------
// SSO provider icons
// ---------------------------------------------------------------------------

/** Google "G" logo as inline SVG (no external dependency) */
function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Login page
// ---------------------------------------------------------------------------

/**
 * Login page for the Praxis web dashboard.
 *
 * Uses Firebase Authentication for SSO-only login:
 * 1. User clicks "Sign in with GitHub" or "Sign in with Google"
 * 2. Firebase opens a popup for the provider's auth flow
 * 3. On success, the Firebase ID token is sent to the Praxis backend
 * 4. Backend verifies the token and returns a Praxis JWT
 * 5. JWT is stored in auth state for API calls
 *
 * Dev-mode quick login is still available when VITE_DEV_MODE=true.
 */
export function LoginPage() {
  const [signingIn, setSigningIn] = useState(false);

  const loginWithFirebase = useAuthStore((s) => s.loginWithFirebase);
  const loginWithToken = useAuthStore((s) => s.loginWithToken);
  const login = useAuthStore((s) => s.login);
  const loading = useAuthStore((s) => s.loading);
  const error = useAuthStore((s) => s.error);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  const navigate = useNavigate();
  const location = useLocation();

  const from =
    (location.state as { from?: { pathname: string } })?.from?.pathname ?? "/";

  const isDevMode = import.meta.env.VITE_DEV_MODE === "true";

  // --- Handle legacy OAuth token from URL fragment (backward compat) ---
  useEffect(() => {
    const hash = window.location.hash;
    if (hash.startsWith("#token=")) {
      const token = hash.substring("#token=".length);
      if (token) {
        loginWithToken(token);
        // Clear the fragment from the URL without triggering a navigation
        window.history.replaceState(null, "", window.location.pathname);
      }
    }
  }, [loginWithToken]);

  // --- Redirect if already authenticated ---
  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  async function handleFirebaseLogin(provider: "github" | "google") {
    setSigningIn(true);
    try {
      const authProvider =
        provider === "github" ? githubProvider : googleProvider;
      const result = await signInWithPopup(auth, authProvider);
      const idToken = await result.user.getIdToken();
      await loginWithFirebase(idToken);
      navigate(from, { replace: true });
    } catch (err) {
      // Firebase popup errors (user closed, network issues, etc.)
      // Auth store already handles API-level errors.
      // Only set a local error if the store didn't catch it.
      const authError = useAuthStore.getState().error;
      if (!authError && err instanceof Error) {
        // Firebase errors have a code property
        const firebaseErr = err as Error & { code?: string };
        if (firebaseErr.code === "auth/popup-closed-by-user") {
          // Not an error -- user just closed the popup
        } else if (firebaseErr.code === "auth/cancelled-popup-request") {
          // Another popup was opened, ignore
        } else {
          useAuthStore.setState({
            error: "Sign-in failed. Please try again.",
          });
        }
      }
    } finally {
      setSigningIn(false);
    }
  }

  async function handleDevLogin() {
    try {
      await login({ username: "dev-user", password: "dev" });
      navigate(from, { replace: true });
    } catch {
      // Error is set in the store
    }
  }

  const isLoading = loading || signingIn;

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--background)] p-4">
      <div className="w-full max-w-sm space-y-6">
        {/* Brand header */}
        <div className="flex flex-col items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--primary)] text-[var(--primary-foreground)]">
            <Network className="h-6 w-6" />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-semibold tracking-tight">Praxis</h1>
            <p className="text-sm text-[var(--muted-foreground)]">
              Sign in to continue
            </p>
          </div>
        </div>

        {/* Error display */}
        {error && (
          <div className="flex items-center gap-2 rounded-md border border-[var(--destructive)] bg-[var(--destructive)]/10 px-4 py-3 text-sm text-[var(--destructive)]">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {/* SSO buttons */}
        <div className="space-y-3">
          <button
            type="button"
            onClick={() => handleFirebaseLogin("github")}
            disabled={isLoading}
            className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md border border-[var(--input)] bg-[var(--background)] px-4 py-2 text-sm font-medium ring-offset-[var(--background)] transition-colors hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Github className="h-4 w-4" />
            )}
            Sign in with GitHub
          </button>

          <button
            type="button"
            onClick={() => handleFirebaseLogin("google")}
            disabled={isLoading}
            className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md border border-[var(--input)] bg-[var(--background)] px-4 py-2 text-sm font-medium ring-offset-[var(--background)] transition-colors hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <GoogleIcon className="h-4 w-4" />
            )}
            Sign in with Google
          </button>
        </div>

        {/* Dev mode quick login */}
        {isDevMode && (
          <div className="space-y-3">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-[var(--border)]" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-[var(--background)] px-2 text-[var(--muted-foreground)]">
                  Development mode
                </span>
              </div>
            </div>
            <button
              type="button"
              onClick={handleDevLogin}
              disabled={isLoading}
              className="inline-flex h-10 w-full items-center justify-center rounded-md border border-[var(--input)] bg-[var(--background)] px-4 py-2 text-sm font-medium ring-offset-[var(--background)] transition-colors hover:bg-[var(--accent)] hover:text-[var(--accent-foreground)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
            >
              Quick login as dev-user
            </button>
          </div>
        )}

        {/* Footer */}
        <p className="text-center text-xs text-[var(--muted-foreground)]">
          Terrene Foundation
        </p>
      </div>
    </div>
  );
}
