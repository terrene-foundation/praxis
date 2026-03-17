// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Tree node element for the delegation tree visualization.
 *
 * Renders a single node (authority or delegate) with constraint annotations
 * and collapsible children.
 */

import { useState } from "react";
import { ChevronDown, ChevronRight, Shield, User } from "lucide-react";

import type { DelegationRecord } from "@/types/api";
import { formatRelativeTime } from "@/lib/format";
import { cn } from "@/lib/utils";

export interface DelegationNode {
  id: string;
  label: string;
  isAuthority: boolean;
  delegation?: DelegationRecord;
  children: DelegationNode[];
}

interface TreeNodeProps {
  node: DelegationNode;
  depth: number;
}

export function TreeNode({ node, depth }: TreeNodeProps) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = node.children.length > 0;

  return (
    <div style={{ marginLeft: depth > 0 ? 24 : 0 }}>
      {/* Node */}
      <button
        type="button"
        onClick={() => hasChildren && setExpanded(!expanded)}
        className={cn(
          "flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors",
          hasChildren
            ? "cursor-pointer hover:bg-[var(--accent)]"
            : "cursor-default",
        )}
      >
        {/* Expand/collapse indicator */}
        <span className="w-4 shrink-0 text-[var(--muted-foreground)]">
          {hasChildren ? (
            expanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )
          ) : (
            <span className="inline-block h-4 w-4" />
          )}
        </span>

        {/* Icon */}
        {node.isAuthority ? (
          <Shield className="h-4 w-4 shrink-0 text-[var(--trust-auto)]" />
        ) : (
          <User className="h-4 w-4 shrink-0 text-[var(--muted-foreground)]" />
        )}

        {/* Label */}
        <span className="font-medium">{node.label}</span>

        {/* Constraint annotation */}
        {node.delegation && (
          <span className="ml-auto text-xs text-[var(--muted-foreground)]">
            {formatRelativeTime(node.delegation.created_at)}
          </span>
        )}
      </button>

      {/* Constraint summary for delegates */}
      {expanded && node.delegation && (
        <div className="mb-1 ml-10 rounded-md bg-[var(--muted)] px-2 py-1 text-xs text-[var(--muted-foreground)]">
          <span className="font-medium">Constraints: </span>
          Spend up to ${node.delegation.constraints.financial.max_spend} |{" "}
          {node.delegation.constraints.operational.allowed_actions.length}{" "}
          allowed operations |{" "}
          {node.delegation.constraints.temporal.max_duration_minutes}min max
        </div>
      )}

      {/* Children */}
      {expanded &&
        node.children.map((child) => (
          <TreeNode key={child.id} node={child} depth={depth + 1} />
        ))}
    </div>
  );
}
