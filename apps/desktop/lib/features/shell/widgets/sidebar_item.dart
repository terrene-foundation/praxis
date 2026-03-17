import 'package:flutter/material.dart';

import '../../../core/design/design_system.dart';
import '../../../core/navigation/routes.dart';

/// A single sidebar navigation item with icon, label, and optional badge.
class SidebarItem extends StatelessWidget {
  final NavDestination destination;
  final bool isActive;
  final bool isCollapsed;
  final int badgeCount;
  final VoidCallback onTap;

  const SidebarItem({
    super.key,
    required this.destination,
    required this.isActive,
    required this.isCollapsed,
    this.badgeCount = 0,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final icon = isActive ? destination.activeIcon : destination.icon;

    final iconWidget = Badge(
      isLabelVisible: badgeCount > 0,
      label: Text(
        badgeCount > 99 ? '99+' : badgeCount.toString(),
        style: const TextStyle(fontSize: 10),
      ),
      child: Icon(
        icon,
        color: isActive
            ? theme.colorScheme.primary
            : theme.colorScheme.onSurfaceVariant,
      ),
    );

    if (isCollapsed) {
      return Tooltip(
        message: destination.label,
        preferBelow: false,
        child: InkWell(
          onTap: onTap,
          child: Container(
            width: PraxisSpacing.sidebarCollapsed,
            height: 48,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: isActive
                  ? theme.colorScheme.primaryContainer.withValues(alpha: 0.3)
                  : null,
              borderRadius: BorderRadius.circular(8),
            ),
            child: iconWidget,
          ),
        ),
      );
    }

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        height: 48,
        margin: const EdgeInsets.symmetric(
          horizontal: PraxisSpacing.sm,
          vertical: 2,
        ),
        padding: const EdgeInsets.symmetric(horizontal: PraxisSpacing.md),
        decoration: BoxDecoration(
          color: isActive
              ? theme.colorScheme.primaryContainer.withValues(alpha: 0.3)
              : null,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            iconWidget,
            const SizedBox(width: PraxisSpacing.md),
            Expanded(
              child: Text(
                destination.label,
                style: theme.textTheme.bodyMedium?.copyWith(
                  fontWeight: isActive ? FontWeight.w600 : FontWeight.w400,
                  color: isActive
                      ? theme.colorScheme.primary
                      : theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
