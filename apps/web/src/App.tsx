// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

import { useEffect } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { AppLayout } from "@/components/layout/AppLayout";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { DashboardPage } from "@/pages/dashboard";
import { LoginPage } from "@/pages/login";
import { NotFoundPage } from "@/pages/not-found";
import { useAuthStore } from "@/stores/auth";

// M11: Practitioner & Supervisor Views
import { PractitionerDashboardPage } from "@/pages/practitioner/dashboard";
import { SessionWizardPage } from "@/pages/practitioner/session-wizard";
import { ConstraintEditorPage } from "@/pages/practitioner/constraint-editor";
import { TeamOverviewPage } from "@/pages/supervisor/team-overview";
import { ApprovalQueuePage } from "@/pages/supervisor/approval-queue";
import { SessionInspectionPage } from "@/pages/supervisor/session-inspection";
import { DelegationManagementPage } from "@/pages/supervisor/delegation-management";
import { ComplianceReportPage } from "@/pages/supervisor/compliance-report";

// M12: Auditor View & Verification
import { VerificationPortalPage } from "@/pages/auditor/verification-portal";
import { BundleTimelinePage } from "@/pages/auditor/bundle-timeline";
import { ConstraintCompliancePage } from "@/pages/auditor/constraint-compliance";
import { ReportDownloadPage } from "@/pages/auditor/report-download";

// M18: Analytics
import { AnalyticsPage } from "@/pages/analytics/analytics";

// ---------------------------------------------------------------------------
// Query client singleton
// ---------------------------------------------------------------------------

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000, // 30 seconds
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

export default function App() {
  const initialize = useAuthStore((s) => s.initialize);

  // Restore auth state from localStorage on mount
  useEffect(() => {
    initialize();
  }, [initialize]);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected routes with app layout */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            {/* Default dashboard (role-aware redirect could go here) */}
            <Route index element={<DashboardPage />} />

            {/* Practitioner routes (M11-01, M11-02, M11-07) */}
            <Route
              path="practitioner"
              element={<PractitionerDashboardPage />}
            />
            <Route path="sessions" element={<PractitionerDashboardPage />} />
            <Route path="sessions/new" element={<SessionWizardPage />} />
            <Route path="sessions/:id" element={<SessionInspectionPage />} />
            <Route
              path="sessions/:id/constraints"
              element={<ConstraintEditorPage />}
            />
            <Route path="decisions" element={<PractitionerDashboardPage />} />
            <Route path="status" element={<PractitionerDashboardPage />} />

            {/* Supervisor routes (M11-08 through M11-13) */}
            <Route path="team" element={<TeamOverviewPage />} />
            <Route path="approvals" element={<ApprovalQueuePage />} />
            <Route path="delegations" element={<DelegationManagementPage />} />
            <Route path="reports" element={<ComplianceReportPage />} />

            {/* Analytics (M18-01) */}
            <Route path="analytics" element={<AnalyticsPage />} />

            {/* Settings placeholder */}
            <Route
              path="settings"
              element={<PlaceholderPage title="Settings" />}
            />
          </Route>

          {/* Auditor routes (no auth required for bundle verification) (M12) */}
          <Route path="/verify" element={<VerificationPortalPage />} />
          <Route path="/verify/timeline" element={<BundleTimelinePage />} />
          <Route
            path="/verify/compliance"
            element={<ConstraintCompliancePage />}
          />
          <Route path="/verify/download" element={<ReportDownloadPage />} />

          {/* Catch-all */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

// ---------------------------------------------------------------------------
// Placeholder for settings page (future milestone)
// ---------------------------------------------------------------------------

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
      <p className="text-sm text-[var(--muted-foreground)]">
        This page will be implemented in a future milestone.
      </p>
    </div>
  );
}
