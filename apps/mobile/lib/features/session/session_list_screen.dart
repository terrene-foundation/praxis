import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';

/// Screen listing active CO sessions on mobile.
class SessionListScreen extends ConsumerWidget {
  const SessionListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sessions = ref.watch(activeSessionsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Sessions')),
      body: sessions.when(
        data: (list) => list.isEmpty
            ? const Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.layers_outlined, size: 48, color: Colors.grey),
                    SizedBox(height: MobileSpacing.md),
                    Text('No active sessions'),
                  ],
                ),
              )
            : PullToRefreshWrapper(
                onRefresh: () => ref.refresh(activeSessionsProvider.future),
                child: ListView.builder(
                  itemCount: list.length,
                  itemBuilder: (context, index) {
                    final session = list[index];
                    return AppListTile(
                      title: session.name,
                      subtitle: session.domain,
                      trailing: SessionStatusBadge(status: session.status),
                      onTap: () => context.go('/sessions/${session.id}'),
                    );
                  },
                ),
              ),
        loading: () => const Padding(
          padding: MobileSpacing.pagePadding,
          child: AppLoading(count: 5),
        ),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }
}
