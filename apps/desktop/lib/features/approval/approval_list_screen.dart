import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';

/// Screen listing pending held actions awaiting approval.
class ApprovalListScreen extends ConsumerWidget {
  const ApprovalListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final approvals = ref.watch(pendingApprovalsProvider);

    return Scaffold(
      body: Padding(
        padding: PraxisSpacing.pagePadding,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Approvals', style: theme.textTheme.headlineMedium),
            const SizedBox(height: PraxisSpacing.lg),
            Expanded(
              child: approvals.when(
                data: (list) => list.isEmpty
                    ? const AppEmptyState(
                        icon: Icons.approval_outlined,
                        title: 'All clear',
                        description: 'No actions are waiting for your approval.',
                      )
                    : ListView.builder(
                        itemCount: list.length,
                        itemBuilder: (context, index) {
                          final action = list[index];
                          return AppCard(
                            onTap: () =>
                                context.go('/approvals/${action.id}'),
                            child: ListTile(
                              title: Text(action.description),
                              subtitle: Text(
                                '${action.actionType} -- ${action.constraintTriggered}',
                              ),
                              trailing: HeldActionStatusBadge(
                                  status: action.status),
                            ),
                          );
                        },
                      ),
                loading: () =>
                    const AppLoading(variant: SkeletonVariant.listItem, count: 3),
                error: (e, _) => Center(child: Text('Error: $e')),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
