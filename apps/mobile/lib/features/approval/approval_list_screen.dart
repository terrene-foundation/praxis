import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';

/// Screen listing pending held actions on mobile.
class ApprovalListScreen extends ConsumerWidget {
  const ApprovalListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final approvals = ref.watch(pendingApprovalsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Approvals')),
      body: approvals.when(
        data: (list) => list.isEmpty
            ? const Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.approval_outlined, size: 48, color: Colors.grey),
                    SizedBox(height: MobileSpacing.md),
                    Text('No pending approvals'),
                  ],
                ),
              )
            : PullToRefreshWrapper(
                onRefresh: () =>
                    ref.refresh(pendingApprovalsProvider.future),
                child: ListView.builder(
                  itemCount: list.length,
                  itemBuilder: (context, index) {
                    final action = list[index];
                    return AppListTile(
                      title: action.description,
                      subtitle: '${action.actionType} -- ${action.constraintTriggered}',
                      trailing:
                          HeldActionStatusBadge(status: action.status),
                      onTap: () =>
                          context.go('/approvals/${action.id}'),
                    );
                  },
                ),
              ),
        loading: () => const Padding(
          padding: MobileSpacing.pagePadding,
          child: AppLoading(count: 3),
        ),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }
}
