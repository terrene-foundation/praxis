import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';

/// Dashboard overview screen showing active sessions and pending approvals.
class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final sessions = ref.watch(activeSessionsProvider);
    final approvals = ref.watch(pendingApprovalsProvider);

    return Scaffold(
      body: Padding(
        padding: PraxisSpacing.pagePadding,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Dashboard', style: theme.textTheme.headlineMedium),
            const SizedBox(height: PraxisSpacing.lg),
            Expanded(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    flex: 2,
                    child: AppCard(
                      title: 'Active Sessions',
                      child: sessions.when(
                        data: (list) => list.isEmpty
                            ? const AppEmptyState(
                                icon: Icons.layers_outlined,
                                title: 'No active sessions',
                              )
                            : Column(
                                children: list
                                    .map((s) => ListTile(
                                          title: Text(s.name),
                                          subtitle: Text(s.domain),
                                          trailing: SessionStatusBadge(
                                              status: s.status),
                                        ))
                                    .toList(),
                              ),
                        loading: () => const AppLoading(
                            variant: SkeletonVariant.listItem, count: 3),
                        error: (e, _) => Center(child: Text('Error: $e')),
                      ),
                    ),
                  ),
                  const SizedBox(width: PraxisSpacing.md),
                  Expanded(
                    child: AppCard(
                      title: 'Pending Approvals',
                      child: approvals.when(
                        data: (list) => list.isEmpty
                            ? const AppEmptyState(
                                icon: Icons.approval_outlined,
                                title: 'No pending approvals',
                              )
                            : Column(
                                children: list
                                    .map((a) => ListTile(
                                          title: Text(a.description),
                                          subtitle: Text(a.constraintTriggered),
                                          trailing: HeldActionStatusBadge(
                                              status: a.status),
                                        ))
                                    .toList(),
                              ),
                        loading: () => const AppLoading(
                            variant: SkeletonVariant.listItem, count: 2),
                        error: (e, _) => Center(child: Text('Error: $e')),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
