// Copyright 2026 Terrene Foundation
// Licensed under the Apache License, Version 2.0

/**
 * Utility functions for the Praxis web dashboard.
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind CSS classes with conflict resolution.
 * This is the standard utility used by shadcn/ui components.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
