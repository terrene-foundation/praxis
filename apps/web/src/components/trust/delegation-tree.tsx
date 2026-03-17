// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * M11-10: Delegation Tree
 *
 * Interactive hierarchy visualization showing authority -> delegates
 * with constraint annotations. Click to expand/collapse branches.
 *
 * Builds the tree from the trust chain data returned by the API.
 */

import { GitBranch } from "lucide-react";

import { useTrustChain } from "@/services/hooks";
import {
  TreeNode,
  type DelegationNode,
} from "@/components/trust/elements/TreeNode";

interface DelegationTreeProps {
  sessionId: string;
}

function buildTree(
  _chain: { chain_length: number; head_hash: string; valid: boolean },
  sessionId: string,
): DelegationNode {
  // Build a simple tree from chain status.
  // In a full implementation, the API would return delegation records
  // that we'd assemble into a tree. For now, we create a root node
  // representing the session authority.
  return {
    id: sessionId,
    label: "Session Authority",
    isAuthority: true,
    children: [],
  };
}

export function DelegationTree({ sessionId }: DelegationTreeProps) {
  const { data, isPending, error } = useTrustChain(sessionId);

  if (isPending) {
    return (
      <div className="space-y-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className="h-4 w-4 animate-pulse rounded bg-[var(--muted)]" />
            <div className="h-4 w-32 animate-pulse rounded bg-[var(--muted)]" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-sm text-[var(--muted-foreground)]">
        Could not load the trust chain. Please try again.
      </p>
    );
  }

  if (!data) return null;

  const tree = buildTree(data, sessionId);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm text-[var(--muted-foreground)]">
        <GitBranch className="h-4 w-4" />
        <span>
          Chain length: {data.chain_length} |{" "}
          {data.valid ? (
            <span className="trust-valid">Valid</span>
          ) : (
            <span className="trust-invalid">
              Broken ({data.breaks.length} break
              {data.breaks.length !== 1 ? "s" : ""})
            </span>
          )}
        </span>
      </div>
      <TreeNode node={tree} depth={0} />
    </div>
  );
}
