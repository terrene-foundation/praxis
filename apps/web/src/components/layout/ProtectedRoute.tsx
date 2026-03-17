// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

import { Navigate, useLocation } from "react-router-dom";

import { useAuthStore } from "@/stores/auth";
import type { UserRole } from "@/types/api";

interface ProtectedRouteProps {
  /** The content to render if authentication passes */
  children: React.ReactNode;
  /** Optional: restrict to specific roles */
  allowedRoles?: UserRole[];
}

/**
 * Route guard that redirects unauthenticated users to the login page.
 *
 * Optionally restricts access to specific user roles. If the user is
 * authenticated but lacks the required role, they are redirected to
 * the dashboard instead.
 */
export function ProtectedRoute({
  children,
  allowedRoles,
}: ProtectedRouteProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const location = useLocation();

  // Not logged in: redirect to login, preserving intended destination
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Logged in but wrong role: redirect to dashboard
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
