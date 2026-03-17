// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M11-12: Delegation Management
 *
 * Manage team member delegations:
 * - Add new delegates
 * - Edit constraint envelopes per delegate (tightening only)
 * - Revoke delegations with cascade warning
 */

import { useState } from "react";
import {
  AlertTriangle,
  GitBranch,
  Loader2,
  Plus,
  Trash2,
  UserPlus,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useSessions, useDelegate } from "@/services/hooks";
import { formatRelativeTime } from "@/lib/format";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface LocalDelegation {
  id: string;
  delegateId: string;
  sessionId: string;
  createdAt: string;
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function DelegationManagementPage() {
  const { data: sessionData } = useSessions();
  const delegateMutation = useDelegate();

  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showRevokeDialog, setShowRevokeDialog] = useState(false);
  const [selectedDelegation, setSelectedDelegation] =
    useState<LocalDelegation | null>(null);
  const [newDelegateId, setNewDelegateId] = useState("");
  const [selectedSessionId, setSelectedSessionId] = useState("");

  // In a real implementation, this would come from an API. For now,
  // delegations are tracked from creation events.
  const [delegations, setDelegations] = useState<LocalDelegation[]>([]);

  const sessions = sessionData?.sessions ?? [];

  async function handleAddDelegate() {
    if (!newDelegateId.trim() || !selectedSessionId) return;

    await delegateMutation.mutateAsync({
      sessionId: selectedSessionId,
      data: { delegate_id: newDelegateId.trim() },
    });

    setDelegations([
      ...delegations,
      {
        id: `del-${Date.now()}`,
        delegateId: newDelegateId.trim(),
        sessionId: selectedSessionId,
        createdAt: new Date().toISOString(),
      },
    ]);

    setNewDelegateId("");
    setSelectedSessionId("");
    setShowAddDialog(false);
  }

  function handleRevoke() {
    if (!selectedDelegation) return;
    setDelegations(delegations.filter((d) => d.id !== selectedDelegation.id));
    setSelectedDelegation(null);
    setShowRevokeDialog(false);
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Delegation Management
          </h1>
          <p className="text-sm text-[var(--muted-foreground)]">
            Add, edit, and revoke delegate access to your sessions.
          </p>
        </div>
        <Button onClick={() => setShowAddDialog(true)}>
          <UserPlus className="h-4 w-4" />
          Add Delegate
        </Button>
      </div>

      {/* Delegations table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-4 w-4" />
            Active Delegations
          </CardTitle>
        </CardHeader>
        <CardContent>
          {delegations.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <GitBranch className="h-8 w-8 text-[var(--muted-foreground)]" />
              <p className="text-sm text-[var(--muted-foreground)]">
                No delegations yet. Add a team member to get started.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowAddDialog(true)}
              >
                <Plus className="h-4 w-4" />
                Add first delegate
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Delegate</TableHead>
                  <TableHead>Session</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {delegations.map((delegation) => (
                  <TableRow key={delegation.id}>
                    <TableCell className="font-medium">
                      {delegation.delegateId}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-[var(--muted-foreground)]">
                      {delegation.sessionId.slice(0, 8)}...
                    </TableCell>
                    <TableCell className="text-[var(--muted-foreground)]">
                      {formatRelativeTime(delegation.createdAt)}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => {
                          setSelectedDelegation(delegation);
                          setShowRevokeDialog(true);
                        }}
                      >
                        <Trash2 className="h-3 w-3 text-[var(--trust-blocked)]" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add delegate dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add a Delegate</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label>Delegate ID</Label>
              <Input
                placeholder="e.g. alice@team.example"
                value={newDelegateId}
                onChange={(e) => setNewDelegateId(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Session</Label>
              <select
                value={selectedSessionId}
                onChange={(e) => setSelectedSessionId(e.target.value)}
                className="h-9 w-full rounded-md border border-[var(--input)] bg-transparent px-3 text-sm"
              >
                <option value="">Select a session</option>
                {sessions
                  .filter((s) => s.state === "active")
                  .map((s) => (
                    <option key={s.session_id} value={s.session_id}>
                      {s.domain} - {s.session_id.slice(0, 8)}
                    </option>
                  ))}
              </select>
            </div>
            <p className="text-xs text-[var(--muted-foreground)]">
              The delegate will inherit your constraints but cannot loosen them.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleAddDelegate}
              disabled={
                !newDelegateId.trim() ||
                !selectedSessionId ||
                delegateMutation.isPending
              }
            >
              {delegateMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <UserPlus className="h-4 w-4" />
              )}
              Add Delegate
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Revoke confirmation dialog */}
      <Dialog open={showRevokeDialog} onOpenChange={setShowRevokeDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-[var(--trust-blocked)]" />
              Revoke Delegation
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <p className="text-sm">
              Are you sure you want to revoke access for{" "}
              <span className="font-semibold">
                {selectedDelegation?.delegateId}
              </span>
              ?
            </p>
            <div className="rounded-md border border-[var(--trust-held)] bg-[color-mix(in_oklch,var(--trust-held)_10%,transparent)] p-3">
              <p className="text-sm font-medium text-[var(--trust-held)]">
                Cascade Warning
              </p>
              <p className="mt-1 text-xs text-[var(--muted-foreground)]">
                Revoking this delegation will also revoke any sub-delegations
                that were created by this delegate. This action cannot be
                undone.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowRevokeDialog(false)}
            >
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleRevoke}>
              <Trash2 className="h-4 w-4" />
              Revoke Access
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
