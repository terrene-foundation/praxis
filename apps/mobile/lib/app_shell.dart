import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:praxis_shared/praxis_shared.dart';

import 'core/navigation/routes.dart';

/// The main mobile app shell with adaptive navigation.
///
/// Uses bottom navigation bar on phones (<600px) and a navigation rail
/// on tablets (>=600px). Preserves tab state using StatefulShellRoute.
class AppShell extends ConsumerWidget {
  final StatefulNavigationShell navigationShell;

  const AppShell({super.key, required this.navigationShell});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pendingCount = ref.watch(pendingApprovalCountProvider);

    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 600) {
          return _TabletShell(
            navigationShell: navigationShell,
            pendingCount: pendingCount,
          );
        }
        return _PhoneShell(
          navigationShell: navigationShell,
          pendingCount: pendingCount,
        );
      },
    );
  }
}

class _PhoneShell extends StatelessWidget {
  final StatefulNavigationShell navigationShell;
  final int pendingCount;

  const _PhoneShell({
    required this.navigationShell,
    required this.pendingCount,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: navigationShell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: navigationShell.currentIndex,
        onDestinationSelected: (index) {
          HapticFeedback.selectionClick();
          navigationShell.goBranch(
            index,
            initialLocation: index == navigationShell.currentIndex,
          );
        },
        destinations: [
          for (final tab in MobileNavTab.values)
            NavigationDestination(
              icon: Badge(
                isLabelVisible:
                    tab == MobileNavTab.approvals && pendingCount > 0,
                label: Text(
                  pendingCount > 99 ? '99+' : pendingCount.toString(),
                  style: const TextStyle(fontSize: 10),
                ),
                child: Icon(tab.icon),
              ),
              selectedIcon: Badge(
                isLabelVisible:
                    tab == MobileNavTab.approvals && pendingCount > 0,
                label: Text(
                  pendingCount > 99 ? '99+' : pendingCount.toString(),
                  style: const TextStyle(fontSize: 10),
                ),
                child: Icon(tab.activeIcon),
              ),
              label: tab.label,
            ),
        ],
      ),
    );
  }
}

class _TabletShell extends StatelessWidget {
  final StatefulNavigationShell navigationShell;
  final int pendingCount;

  const _TabletShell({
    required this.navigationShell,
    required this.pendingCount,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: navigationShell.currentIndex,
            onDestinationSelected: (index) {
              HapticFeedback.selectionClick();
              navigationShell.goBranch(
                index,
                initialLocation: index == navigationShell.currentIndex,
              );
            },
            labelType: NavigationRailLabelType.all,
            destinations: [
              for (final tab in MobileNavTab.values)
                NavigationRailDestination(
                  icon: Badge(
                    isLabelVisible:
                        tab == MobileNavTab.approvals && pendingCount > 0,
                    label: Text(
                      pendingCount > 99 ? '99+' : pendingCount.toString(),
                      style: const TextStyle(fontSize: 10),
                    ),
                    child: Icon(tab.icon),
                  ),
                  selectedIcon: Badge(
                    isLabelVisible:
                        tab == MobileNavTab.approvals && pendingCount > 0,
                    label: Text(
                      pendingCount > 99 ? '99+' : pendingCount.toString(),
                      style: const TextStyle(fontSize: 10),
                    ),
                    child: Icon(tab.activeIcon),
                  ),
                  label: Text(tab.label),
                ),
            ],
          ),
          const VerticalDivider(width: 1, thickness: 1),
          Expanded(child: navigationShell),
        ],
      ),
    );
  }
}
