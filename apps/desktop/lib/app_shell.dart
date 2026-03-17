import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/providers/app_providers.dart';
import 'features/shell/widgets/sidebar.dart';

/// The main desktop app shell -- persistent sidebar + content area.
class AppShell extends ConsumerWidget {
  final Widget child;

  const AppShell({super.key, required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isCollapsed = ref.watch(sidebarCollapsedProvider);
    final currentPath = GoRouterState.of(context).matchedLocation;

    return Scaffold(
      body: Row(
        children: [
          Sidebar(
            isCollapsed: isCollapsed,
            currentPath: currentPath,
            onToggleCollapse: () {
              ref.read(sidebarCollapsedProvider.notifier).toggle();
            },
            onNavigate: (destination) {
              context.go(destination.path);
            },
          ),
          const VerticalDivider(width: 1, thickness: 1),
          Expanded(
            child: child,
          ),
        ],
      ),
    );
  }
}
