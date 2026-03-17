// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

import { Link, useLocation } from "react-router-dom";
import {
  Activity,
  BarChart3,
  CheckSquare,
  FileText,
  GitBranch,
  LayoutDashboard,
  LogOut,
  Network,
  Settings,
  Shield,
  Users,
} from "lucide-react";

import { useAuthStore } from "@/stores/auth";
import { cn } from "@/lib/utils";
import type { UserRole } from "@/types/api";

// ---------------------------------------------------------------------------
// Navigation items by role
// ---------------------------------------------------------------------------

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const practitionerNav: NavItem[] = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Sessions", href: "/sessions", icon: Activity },
  { label: "Decisions", href: "/decisions", icon: CheckSquare },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Status", href: "/status", icon: FileText },
];

const supervisorNav: NavItem[] = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Team", href: "/team", icon: Users },
  { label: "Approvals", href: "/approvals", icon: CheckSquare },
  { label: "Delegations", href: "/delegations", icon: GitBranch },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Reports", href: "/reports", icon: FileText },
];

const auditorNav: NavItem[] = [
  { label: "Verify", href: "/verify", icon: Shield },
];

const navByRole: Record<UserRole, NavItem[]> = {
  practitioner: practitionerNav,
  supervisor: supervisorNav,
  auditor: auditorNav,
  admin: [...practitionerNav, ...supervisorNav, ...auditorNav],
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function Sidebar() {
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const role = user?.role ?? "practitioner";
  const items = navByRole[role];

  return (
    <aside className="flex h-full w-64 flex-col border-r border-[var(--sidebar-border)] bg-[var(--sidebar)] text-[var(--sidebar-foreground)]">
      {/* Brand */}
      <div className="flex h-16 items-center gap-3 border-b border-[var(--sidebar-border)] px-6">
        <Network className="h-6 w-6 text-[var(--sidebar-primary)]" />
        <span className="text-lg font-semibold tracking-tight">Praxis</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {items.map((item) => {
          const isActive =
            item.href === "/"
              ? location.pathname === "/"
              : location.pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-[var(--sidebar-accent)] text-[var(--sidebar-accent-foreground)]"
                  : "text-[var(--sidebar-foreground)] hover:bg-[var(--sidebar-accent)] hover:text-[var(--sidebar-accent-foreground)]",
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-[var(--sidebar-border)] p-3">
        <Link
          to="/settings"
          className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-[var(--muted-foreground)] transition-colors hover:bg-[var(--sidebar-accent)] hover:text-[var(--sidebar-accent-foreground)]"
        >
          <Settings className="h-4 w-4" />
          Settings
        </Link>
        <button
          type="button"
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-[var(--muted-foreground)] transition-colors hover:bg-[var(--sidebar-accent)] hover:text-[var(--sidebar-accent-foreground)]"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
