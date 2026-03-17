import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';

/// Screen listing all CO sessions.
class SessionListScreen extends ConsumerWidget {
  const SessionListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final sessions = ref.watch(activeSessionsProvider);

    return Scaffold(
      body: Padding(
        padding: PraxisSpacing.pagePadding,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Sessions',
                    style: theme.textTheme.headlineMedium,
                  ),
                ),
                AppButton(
                  icon: Icons.add,
                  label: 'New Session',
                  onPressed: () => context.go('/sessions/new'),
                ),
              ],
            ),
            const SizedBox(height: PraxisSpacing.lg),
            Expanded(
              child: sessions.when(
                data: (list) => list.isEmpty
                    ? const AppEmptyState(
                        icon: Icons.layers_outlined,
                        title: 'No sessions yet',
                        description: 'Create a session to begin collaborating.',
                      )
                    : ListView.builder(
                        itemCount: list.length,
                        itemBuilder: (context, index) {
                          final session = list[index];
                          return AppCard(
                            onTap: () =>
                                context.go('/sessions/${session.id}'),
                            child: ListTile(
                              title: Text(session.name),
                              subtitle: Text(session.domain),
                              trailing: SessionStatusBadge(
                                  status: session.status),
                            ),
                          );
                        },
                      ),
                loading: () =>
                    const AppLoading(variant: SkeletonVariant.listItem, count: 5),
                error: (e, _) => Center(child: Text('Error loading sessions: $e')),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
