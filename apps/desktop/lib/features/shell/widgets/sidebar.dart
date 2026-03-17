import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../../core/design/design_system.dart';
import '../../../core/navigation/routes.dart';
import 'sidebar_item.dart';
import 'user_profile_badge.dart';

/// Desktop sidebar navigation.
class Sidebar extends ConsumerWidget {
  final bool isCollapsed;
  final String currentPath;
  final VoidCallback onToggleCollapse;
  final ValueChanged<NavDestination> onNavigate;

  const Sidebar({
    super.key,
    required this.isCollapsed,
    required this.currentPath,
    required this.onToggleCollapse,
    required this.onNavigate,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final pendingCount = ref.watch(pendingApprovalCountProvider);
    final width = isCollapsed
        ? PraxisSpacing.sidebarCollapsed
        : PraxisSpacing.sidebarExpanded;

    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      curve: Curves.easeInOut,
      width: width,
      child: Column(
        children: [
          // Logo and collapse toggle
          Padding(
            padding: const EdgeInsets.all(PraxisSpacing.md),
            child: Row(
              children: [
                Icon(
                  Icons.shield_outlined,
                  color: theme.colorScheme.primary,
                  size: 28,
                ),
                if (!isCollapsed) ...[
                  const SizedBox(width: PraxisSpacing.sm),
                  Expanded(
                    child: Text(
                      'Praxis',
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
                IconButton(
                  icon: Icon(
                    isCollapsed
                        ? Icons.chevron_right
                        : Icons.chevron_left,
                    size: 20,
                  ),
                  onPressed: onToggleCollapse,
                  tooltip: isCollapsed ? 'Expand sidebar' : 'Collapse sidebar',
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          // Main navigation items
          Expanded(
            child: ListView(
              padding: const EdgeInsets.symmetric(vertical: PraxisSpacing.sm),
              children: [
                for (final dest in NavDestination.values)
                  if (dest != NavDestination.settings)
                    SidebarItem(
                      destination: dest,
                      isActive: _isActive(dest),
                      isCollapsed: isCollapsed,
                      badgeCount:
                          dest == NavDestination.approvals ? pendingCount : 0,
                      onTap: () => onNavigate(dest),
                    ),
              ],
            ),
          ),

          // Settings (pinned near bottom)
          const Divider(height: 1),
          SidebarItem(
            destination: NavDestination.settings,
            isActive: _isActive(NavDestination.settings),
            isCollapsed: isCollapsed,
            onTap: () => onNavigate(NavDestination.settings),
          ),

          // User profile
          const Divider(height: 1),
          UserProfileBadge(isCollapsed: isCollapsed),
        ],
      ),
    );
  }

  bool _isActive(NavDestination dest) {
    if (dest == NavDestination.dashboard) return currentPath == '/';
    return currentPath.startsWith(dest.path);
  }
}
