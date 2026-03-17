import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';

/// Provider to fetch trust chain entries for the first active session.
///
/// The trust chain is scoped to sessions. This provider watches for the first
/// active session and fetches its trust chain entries.
final _activeTrustChainProvider =
    FutureProvider<List<TrustEntry>>((ref) async {
  final client = ref.watch(praxisClientProvider);
  final sessions = await client.sessions.listActive();
  if (sessions.isEmpty) return [];
  return client.trust.getChain(sessions.first.id);
});

/// Screen listing trust chain entries on mobile.
class TrustChainListScreen extends ConsumerWidget {
  const TrustChainListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final chainAsync = ref.watch(_activeTrustChainProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Trust Chain')),
      body: chainAsync.when(
        data: (entries) => entries.isEmpty
            ? const Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.shield_outlined,
                        size: 48, color: Colors.grey),
                    SizedBox(height: MobileSpacing.md),
                    Text('No trust chain entries.'),
                    SizedBox(height: MobileSpacing.xs),
                    Text(
                      'Start a session to see trust chain activity.',
                      style: TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                  ],
                ),
              )
            : PullToRefreshWrapper(
                onRefresh: () =>
                    ref.refresh(_activeTrustChainProvider.future),
                child: ListView.separated(
                  itemCount: entries.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final entry = entries[index];
                    return _TrustEntryTile(
                      entry: entry,
                      onTap: () => context.go('/trust/${entry.id}'),
                    );
                  },
                ),
              ),
        loading: () => const Padding(
          padding: MobileSpacing.pagePadding,
          child: AppLoading(count: 5),
        ),
        error: (e, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: MobileSpacing.md),
              Text('Error: $e'),
              const SizedBox(height: MobileSpacing.md),
              FilledButton(
                onPressed: () => ref.invalidate(_activeTrustChainProvider),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// A single trust chain entry tile.
class _TrustEntryTile extends StatelessWidget {
  final TrustEntry entry;
  final VoidCallback? onTap;

  const _TrustEntryTile({required this.entry, this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return ListTile(
      onTap: onTap,
      contentPadding:
          const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: _EntryTypeBadge(type: entry.type),
      title: Text(
        entry.hash.length > 12
            ? '${entry.hash.substring(0, 12)}...'
            : entry.hash,
        style: theme.textTheme.bodyMedium?.copyWith(
          fontFamily: 'monospace',
          fontFamilyFallback: ['Courier'],
        ),
      ),
      subtitle: Text(
        _formatTimestamp(entry.createdAt),
        style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey),
      ),
      trailing: const Icon(Icons.chevron_right, size: 20),
    );
  }

  String _formatTimestamp(DateTime dt) {
    final local = dt.toLocal();
    return '${local.month}/${local.day} '
        '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }
}

/// Color-coded badge for trust entry type.
class _EntryTypeBadge extends StatelessWidget {
  final TrustEntryType type;

  const _EntryTypeBadge({required this.type});

  @override
  Widget build(BuildContext context) {
    final (color, label) = switch (type) {
      TrustEntryType.genesis => (Colors.blue, 'GEN'),
      TrustEntryType.delegation => (Colors.purple, 'DEL'),
      TrustEntryType.constraint => (Colors.orange, 'CON'),
      TrustEntryType.attestation => (Colors.green, 'ATT'),
      TrustEntryType.action => (Colors.teal, 'ACT'),
      TrustEntryType.approval => (Colors.indigo, 'APR'),
    };

    return Container(
      width: 44,
      height: 44,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(10),
      ),
      alignment: Alignment.center,
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}
