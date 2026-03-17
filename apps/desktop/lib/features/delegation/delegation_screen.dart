import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';

/// Screen for managing delegations — listing existing ones and creating new ones.
class DelegationScreen extends ConsumerWidget {
  const DelegationScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final delegations = ref.watch(delegationsProvider);

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
                    'Delegations',
                    style: theme.textTheme.headlineMedium,
                  ),
                ),
                AppButton(
                  label: 'Create Delegation',
                  icon: Icons.person_add,
                  onPressed: () => _showCreateDialog(context, ref),
                ),
              ],
            ),
            const SizedBox(height: PraxisSpacing.lg),
            Expanded(
              child: delegations.when(
                data: (list) => list.isEmpty
                    ? const AppEmptyState(
                        icon: Icons.people_outline,
                        title: 'No delegations yet',
                        description:
                            'Delegations let you grant limited authority to other principals. Create one to get started.',
                      )
                    : _DelegationListAndChain(delegations: list),
                loading: () => const AppLoading(
                  variant: SkeletonVariant.listItem,
                  count: 3,
                ),
                error: (e, _) => AppEmptyState(
                  icon: Icons.error_outline,
                  title: 'Failed to load delegations',
                  description: e is PraxisApiException
                      ? e.userMessage
                      : 'Could not reach the server.',
                  actionLabel: 'Retry',
                  onAction: () => ref.invalidate(delegationsProvider),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showCreateDialog(BuildContext context, WidgetRef ref) {
    showDialog<void>(
      context: context,
      builder: (ctx) => _CreateDelegationDialog(ref: ref),
    );
  }
}

/// Combined list and chain visualization.
class _DelegationListAndChain extends StatelessWidget {
  final List<Delegation> delegations;

  const _DelegationListAndChain({required this.delegations});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          flex: 3,
          child: _DelegationList(delegations: delegations),
        ),
        const SizedBox(width: PraxisSpacing.lg),
        Expanded(
          flex: 2,
          child: _DelegationChainVisualization(delegations: delegations),
        ),
      ],
    );
  }
}

/// Scrollable list of delegation cards.
class _DelegationList extends ConsumerWidget {
  final List<Delegation> delegations;

  const _DelegationList({required this.delegations});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ListView.builder(
      itemCount: delegations.length,
      itemBuilder: (context, index) {
        final d = delegations[index];
        return Padding(
          padding: const EdgeInsets.only(bottom: PraxisSpacing.sm),
          child: _DelegationCard(
            delegation: d,
            onRevoke: d.isActive
                ? () => _revoke(context, ref, d)
                : null,
          ),
        );
      },
    );
  }

  Future<void> _revoke(
    BuildContext context,
    WidgetRef ref,
    Delegation delegation,
  ) async {
    final confirmed = await showAppDialog(
      context: context,
      title: 'Revoke delegation',
      message:
          'This will remove all authority granted to ${delegation.delegateeName}. This cannot be undone.',
      confirmLabel: 'Revoke',
      isDestructive: true,
    );

    if (confirmed == true) {
      final client = ref.read(praxisClientProvider);
      try {
        await client.delegations.revoke(delegation.id);
        ref.invalidate(delegationsProvider);
      } catch (e) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                e is PraxisApiException
                    ? e.userMessage
                    : 'Failed to revoke delegation.',
              ),
            ),
          );
        }
      }
    }
  }
}

/// Card for a single delegation showing delegator, delegatee, status, and constraints.
class _DelegationCard extends StatelessWidget {
  final Delegation delegation;
  final VoidCallback? onRevoke;

  const _DelegationCard({
    required this.delegation,
    this.onRevoke,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final cs = delegation.constraints;
    final financialPct =
        cs.financial.maxAmount > 0 ? cs.financial.currentUsage / cs.financial.maxAmount : 0.0;

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.person, size: 18),
              const SizedBox(width: PraxisSpacing.xs),
              Expanded(
                child: Text.rich(
                  TextSpan(
                    children: [
                      TextSpan(
                        text: delegation.delegatorName,
                        style: theme.textTheme.bodyMedium
                            ?.copyWith(fontWeight: FontWeight.w600),
                      ),
                      const TextSpan(text: '  →  '),
                      TextSpan(
                        text: delegation.delegateeName,
                        style: theme.textTheme.bodyMedium
                            ?.copyWith(fontWeight: FontWeight.w600),
                      ),
                    ],
                  ),
                ),
              ),
              AppBadge(
                text: delegation.isActive ? 'Active' : 'Revoked',
                variant: delegation.isActive
                    ? AppBadgeVariant.success
                    : AppBadgeVariant.neutral,
              ),
            ],
          ),
          const SizedBox(height: PraxisSpacing.sm),
          // Constraint summary
          ConstraintDotsIndicator(
            values: [
              financialPct,
              cs.operational.allowedActions.length / 5,
              (cs.temporal.maxDurationMinutes ?? 0) / 480,
              cs.dataAccess.allowedResources.length / 10,
              cs.communication.allowedChannels.length / 3,
            ],
          ),
          const SizedBox(height: PraxisSpacing.sm),
          Text(
            'Created ${_formatDate(delegation.createdAt)}',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.outline,
            ),
          ),
          if (onRevoke != null) ...[
            const SizedBox(height: PraxisSpacing.sm),
            Align(
              alignment: Alignment.centerRight,
              child: AppButton(
                label: 'Revoke',
                variant: AppButtonVariant.destructive,
                size: AppButtonSize.small,
                onPressed: onRevoke,
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _formatDate(DateTime dt) {
    return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-'
        '${dt.day.toString().padLeft(2, '0')}';
  }
}

/// Simple tree visualization of the delegation chain.
class _DelegationChainVisualization extends StatelessWidget {
  final List<Delegation> delegations;

  const _DelegationChainVisualization({required this.delegations});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    // Build a tree from the delegation data.
    // Root nodes are unique delegators that are not delegatees of anyone.
    final delegateeIds = delegations.map((d) => d.delegateeId).toSet();
    final roots = <String>{};
    for (final d in delegations) {
      if (!delegateeIds.contains(d.delegatorId)) {
        roots.add(d.delegatorId);
      }
    }
    // If no clear root, use all delegators.
    if (roots.isEmpty) {
      roots.addAll(delegations.map((d) => d.delegatorId));
    }

    return AppCard(
      title: 'Delegation Chain',
      child: delegations.isEmpty
          ? Text(
              'No delegations to visualize.',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.outline,
              ),
            )
          : Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (final rootId in roots)
                  _buildChainNode(
                    context,
                    rootId,
                    _nameForId(rootId),
                    0,
                  ),
              ],
            ),
    );
  }

  Widget _buildChainNode(
    BuildContext context,
    String principalId,
    String name,
    int depth,
  ) {
    final theme = Theme.of(context);
    final children = delegations
        .where((d) => d.delegatorId == principalId && d.isActive)
        .toList();

    return Padding(
      padding: EdgeInsets.only(left: depth * 24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (depth > 0) ...[
                Icon(
                  Icons.subdirectory_arrow_right,
                  size: 16,
                  color: theme.colorScheme.outline,
                ),
                const SizedBox(width: PraxisSpacing.xs),
              ],
              Icon(
                depth == 0 ? Icons.shield : Icons.person_outline,
                size: 16,
                color: depth == 0
                    ? PraxisColors.trustHealthy
                    : theme.colorScheme.primary,
              ),
              const SizedBox(width: PraxisSpacing.xs),
              Text(
                name,
                style: theme.textTheme.bodyMedium?.copyWith(
                  fontWeight:
                      depth == 0 ? FontWeight.w600 : FontWeight.normal,
                ),
              ),
              if (depth == 0)
                Padding(
                  padding: const EdgeInsets.only(left: PraxisSpacing.xs),
                  child: Text(
                    '(genesis)',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.outline,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: PraxisSpacing.xs),
          for (final child in children)
            _buildChainNode(
              context,
              child.delegateeId,
              child.delegateeName,
              depth + 1,
            ),
        ],
      ),
    );
  }

  String _nameForId(String id) {
    // Find the delegator name from any delegation where this id is the delegator.
    for (final d in delegations) {
      if (d.delegatorId == id) return d.delegatorName;
    }
    // Or delegatee.
    for (final d in delegations) {
      if (d.delegateeId == id) return d.delegateeName;
    }
    return id;
  }
}

/// Dialog for creating a new delegation.
class _CreateDelegationDialog extends ConsumerStatefulWidget {
  final WidgetRef ref;

  const _CreateDelegationDialog({required this.ref});

  @override
  ConsumerState<_CreateDelegationDialog> createState() =>
      _CreateDelegationDialogState();
}

class _CreateDelegationDialogState
    extends ConsumerState<_CreateDelegationDialog> {
  final _delegateIdController = TextEditingController();
  bool _isCreating = false;
  String? _error;

  // Default constraint values for the new delegation.
  double _maxSpend = 100;
  int _maxDurationMinutes = 60;
  final Map<String, bool> _allowedActions = {
    'read': true,
    'write': false,
    'execute': false,
    'delete': false,
    'deploy': false,
  };

  @override
  void dispose() {
    _delegateIdController.dispose();
    super.dispose();
  }

  Future<void> _create() async {
    final delegateeId = _delegateIdController.text.trim();
    if (delegateeId.isEmpty) {
      setState(() => _error = 'Delegate ID is required.');
      return;
    }

    setState(() {
      _isCreating = true;
      _error = null;
    });

    final allowed = _allowedActions.entries
        .where((e) => e.value)
        .map((e) => e.key)
        .toList();
    final blocked = _allowedActions.entries
        .where((e) => !e.value)
        .map((e) => e.key)
        .toList();

    final constraints = ConstraintSet(
      financial: FinancialConstraint(
        maxAmount: _maxSpend,
        currentUsage: 0,
        currency: 'USD',
      ),
      operational: OperationalConstraint(
        allowedActions: allowed,
        blockedActions: blocked,
      ),
      temporal: TemporalConstraint(maxDurationMinutes: _maxDurationMinutes),
      dataAccess: const DataAccessConstraint(
        allowedResources: [],
        blockedResources: [],
      ),
      communication: const CommunicationConstraint(
        allowedChannels: ['internal'],
        blockedChannels: ['email', 'external'],
      ),
    );

    try {
      final client = ref.read(praxisClientProvider);
      await client.delegations.create(
        delegateeId: delegateeId,
        constraints: constraints,
      );
      ref.invalidate(delegationsProvider);
      if (mounted) Navigator.of(context).pop();
    } catch (e) {
      if (mounted) {
        setState(() {
          _isCreating = false;
          _error = e is PraxisApiException
              ? e.userMessage
              : 'Failed to create delegation.';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AlertDialog(
      title: const Text('Create Delegation'),
      content: SizedBox(
        width: 480,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AppInput(
                label: 'Delegate ID',
                hint: 'Enter the principal ID to delegate to',
                controller: _delegateIdController,
                enabled: !_isCreating,
              ),
              const SizedBox(height: PraxisSpacing.lg),
              Text(
                'Constraint Summary',
                style: theme.textTheme.titleSmall,
              ),
              const SizedBox(height: PraxisSpacing.sm),
              // Financial
              Text(
                'Financial: up to ${_maxSpend.toStringAsFixed(0)} USD',
                style: theme.textTheme.bodySmall,
              ),
              Slider(
                value: _maxSpend,
                min: 0,
                max: 1000,
                divisions: 100,
                label: '${_maxSpend.toStringAsFixed(0)} USD',
                onChanged:
                    _isCreating ? null : (v) => setState(() => _maxSpend = v),
              ),
              // Temporal
              Text(
                'Temporal: up to $_maxDurationMinutes minutes',
                style: theme.textTheme.bodySmall,
              ),
              Slider(
                value: _maxDurationMinutes.toDouble(),
                min: 0,
                max: 480,
                divisions: 32,
                label: '$_maxDurationMinutes min',
                onChanged: _isCreating
                    ? null
                    : (v) =>
                        setState(() => _maxDurationMinutes = v.round()),
              ),
              const SizedBox(height: PraxisSpacing.sm),
              // Operational
              Text('Allowed actions:', style: theme.textTheme.bodySmall),
              const SizedBox(height: PraxisSpacing.xs),
              Wrap(
                spacing: PraxisSpacing.xs,
                children: _allowedActions.entries.map((entry) {
                  return FilterChip(
                    label: Text(entry.key),
                    selected: entry.value,
                    onSelected: _isCreating
                        ? null
                        : (val) => setState(
                            () => _allowedActions[entry.key] = val),
                  );
                }).toList(),
              ),
              if (_error != null) ...[
                const SizedBox(height: PraxisSpacing.md),
                Text(
                  _error!,
                  style: TextStyle(color: theme.colorScheme.error),
                ),
              ],
            ],
          ),
        ),
      ),
      actions: [
        AppButton(
          label: 'Cancel',
          variant: AppButtonVariant.text,
          onPressed: _isCreating ? null : () => Navigator.of(context).pop(),
        ),
        AppButton(
          label: 'Create',
          isLoading: _isCreating,
          onPressed: _isCreating ? null : _create,
        ),
      ],
    );
  }
}
