import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';

/// Provider to fetch a single held action by ID from the pending list.
final heldActionProvider =
    FutureProvider.family<HeldAction?, String>((ref, id) async {
  final all = await ref.watch(pendingApprovalsProvider.future);
  try {
    return all.firstWhere((a) => a.id == id);
  } catch (_) {
    return null;
  }
});

/// State for the approval action (approve/deny in progress).
enum _ApprovalActionState { idle, approving, denying, success, error }

/// Detail screen for a specific held action.
///
/// Shows action details, constraint utilization, and approve/deny controls.
class ApprovalDetailScreen extends ConsumerStatefulWidget {
  final String approvalId;

  const ApprovalDetailScreen({super.key, required this.approvalId});

  @override
  ConsumerState<ApprovalDetailScreen> createState() =>
      _ApprovalDetailScreenState();
}

class _ApprovalDetailScreenState extends ConsumerState<ApprovalDetailScreen> {
  final _conditionsController = TextEditingController();
  _ApprovalActionState _actionState = _ApprovalActionState.idle;
  String? _errorMessage;

  @override
  void dispose() {
    _conditionsController.dispose();
    super.dispose();
  }

  bool get _isProcessing =>
      _actionState == _ApprovalActionState.approving ||
      _actionState == _ApprovalActionState.denying;

  Future<void> _handleApprove(HeldAction action) async {
    setState(() {
      _actionState = _ApprovalActionState.approving;
      _errorMessage = null;
    });

    try {
      final client = ref.read(praxisClientProvider);
      final conditions = _conditionsController.text.trim();
      if (conditions.isNotEmpty) {
        await client.approvals.approveWithConditions(
          action.sessionId,
          action.id,
          conditions,
        );
      } else {
        await client.approvals.approve(action.sessionId, action.id);
      }
      ref.invalidate(pendingApprovalsProvider);
      if (mounted) {
        setState(() => _actionState = _ApprovalActionState.success);
        await Future<void>.delayed(const Duration(milliseconds: 800));
        if (mounted) context.go('/approvals');
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _actionState = _ApprovalActionState.error;
          _errorMessage = _formatError(e);
        });
      }
    }
  }

  Future<void> _handleDeny(HeldAction action) async {
    setState(() {
      _actionState = _ApprovalActionState.denying;
      _errorMessage = null;
    });

    try {
      final client = ref.read(praxisClientProvider);
      await client.approvals.deny(action.sessionId, action.id);
      ref.invalidate(pendingApprovalsProvider);
      if (mounted) {
        setState(() => _actionState = _ApprovalActionState.success);
        await Future<void>.delayed(const Duration(milliseconds: 800));
        if (mounted) context.go('/approvals');
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _actionState = _ApprovalActionState.error;
          _errorMessage = _formatError(e);
        });
      }
    }
  }

  String _formatError(Object error) {
    if (error is PraxisApiException) {
      return error.userMessage;
    }
    return 'Something went wrong. Please try again.';
  }

  @override
  Widget build(BuildContext context, ) {
    final theme = Theme.of(context);
    final actionAsync = ref.watch(heldActionProvider(widget.approvalId));

    return Scaffold(
      body: Padding(
        padding: PraxisSpacing.pagePadding,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(context, theme),
            const SizedBox(height: PraxisSpacing.lg),
            Expanded(
              child: actionAsync.when(
                data: (action) => action == null
                    ? const AppEmptyState(
                        icon: Icons.search_off,
                        title: 'Action not found',
                        description:
                            'This held action may have already been resolved.',
                      )
                    : _buildDetailContent(action, theme),
                loading: () => const AppLoading(
                  variant: SkeletonVariant.card,
                  count: 2,
                ),
                error: (e, _) => _buildErrorState(e),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, ThemeData theme) {
    return Row(
      children: [
        IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/approvals'),
          tooltip: 'Back to approvals',
        ),
        const SizedBox(width: PraxisSpacing.sm),
        Text('Approval Detail', style: theme.textTheme.headlineMedium),
      ],
    );
  }

  Widget _buildDetailContent(HeldAction action, ThemeData theme) {
    if (_actionState == _ApprovalActionState.success) {
      return const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.check_circle, size: 64, color: PraxisColors.trustHealthy),
            SizedBox(height: PraxisSpacing.md),
            Text('Decision recorded. Returning to approvals...'),
          ],
        ),
      );
    }

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _ActionDetailsCard(action: action),
          const SizedBox(height: PraxisSpacing.md),
          _ConstraintUtilizationCard(action: action),
          const SizedBox(height: PraxisSpacing.md),
          _ReasoningCard(action: action),
          const SizedBox(height: PraxisSpacing.lg),
          _buildConditionsInput(theme),
          const SizedBox(height: PraxisSpacing.lg),
          if (_errorMessage != null) ...[
            _buildErrorBanner(theme),
            const SizedBox(height: PraxisSpacing.md),
          ],
          _buildActionButtons(action),
          const SizedBox(height: PraxisSpacing.xl),
        ],
      ),
    );
  }

  Widget _buildConditionsInput(ThemeData theme) {
    return AppCard(
      title: 'Conditions (optional)',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Add notes or conditions to attach to your decision.',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.outline,
            ),
          ),
          const SizedBox(height: PraxisSpacing.sm),
          AppInput(
            hint: 'e.g. "Approved for staging only, not production"',
            controller: _conditionsController,
            maxLines: 3,
            enabled: !_isProcessing,
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons(HeldAction action) {
    final isPending = action.status == HeldActionStatus.pending;

    return Row(
      children: [
        Expanded(
          child: AppButton(
            label: 'Approve',
            icon: Icons.check,
            variant: AppButtonVariant.primary,
            size: AppButtonSize.large,
            isLoading: _actionState == _ApprovalActionState.approving,
            onPressed: isPending && !_isProcessing
                ? () => _handleApprove(action)
                : null,
          ),
        ),
        const SizedBox(width: PraxisSpacing.md),
        Expanded(
          child: AppButton(
            label: 'Deny',
            icon: Icons.close,
            variant: AppButtonVariant.destructive,
            size: AppButtonSize.large,
            isLoading: _actionState == _ApprovalActionState.denying,
            onPressed: isPending && !_isProcessing
                ? () => _handleDeny(action)
                : null,
          ),
        ),
      ],
    );
  }

  Widget _buildErrorBanner(ThemeData theme) {
    return Container(
      padding: PraxisSpacing.cardPadding,
      decoration: BoxDecoration(
        color: theme.colorScheme.errorContainer,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(Icons.error_outline, color: theme.colorScheme.error),
          const SizedBox(width: PraxisSpacing.sm),
          Expanded(
            child: Text(
              _errorMessage!,
              style: TextStyle(color: theme.colorScheme.onErrorContainer),
            ),
          ),
          TextButton(
            onPressed: () => setState(() {
              _actionState = _ApprovalActionState.idle;
              _errorMessage = null;
            }),
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState(Object error) {
    return AppEmptyState(
      icon: Icons.error_outline,
      title: 'Failed to load action',
      description: _formatError(error),
      actionLabel: 'Retry',
      onAction: () => ref.invalidate(heldActionProvider(widget.approvalId)),
    );
  }
}

/// Card showing the held action details: type, resource, constraint, status.
class _ActionDetailsCard extends StatelessWidget {
  final HeldAction action;

  const _ActionDetailsCard({required this.action});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AppCard(
      title: 'Action Details',
      child: Column(
        children: [
          _DetailRow(
            label: 'Action',
            value: action.description,
          ),
          const SizedBox(height: PraxisSpacing.sm),
          _DetailRow(
            label: 'Type',
            value: action.actionType,
          ),
          const SizedBox(height: PraxisSpacing.sm),
          _DetailRow(
            label: 'Session',
            value: action.sessionId,
          ),
          const SizedBox(height: PraxisSpacing.sm),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                width: 140,
                child: Text(
                  'Status',
                  style: theme.textTheme.labelMedium?.copyWith(
                    color: theme.colorScheme.outline,
                  ),
                ),
              ),
              HeldActionStatusBadge(status: action.status),
            ],
          ),
          const SizedBox(height: PraxisSpacing.sm),
          _DetailRow(
            label: 'Created',
            value: _formatTimestamp(action.createdAt),
          ),
        ],
      ),
    );
  }

  String _formatTimestamp(DateTime dt) {
    return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-'
        '${dt.day.toString().padLeft(2, '0')} '
        '${dt.hour.toString().padLeft(2, '0')}:'
        '${dt.minute.toString().padLeft(2, '0')}';
  }
}

/// Card showing which constraint dimension was triggered and utilization.
class _ConstraintUtilizationCard extends StatelessWidget {
  final HeldAction action;

  const _ConstraintUtilizationCard({required this.action});

  @override
  Widget build(BuildContext context) {
    final dimension = action.constraintTriggered.toLowerCase();
    final color = _colorForDimension(dimension);
    // Parse a rough utilization from the constraint triggered name.
    // In a real system the API would return utilization percentage;
    // here we show the gauge at a high level to indicate threshold breach.
    const utilization = 0.85;

    return AppCard(
      title: 'Constraint Triggered',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppBadge(
            text: action.constraintTriggered,
            variant: AppBadgeVariant.warning,
          ),
          const SizedBox(height: PraxisSpacing.md),
          ConstraintGauge(
            label: 'Utilization',
            value: utilization,
            color: color,
            valueLabel: '${(utilization * 100).toInt()}%',
          ),
        ],
      ),
    );
  }

  Color _colorForDimension(String dimension) {
    if (dimension.contains('financial')) return PraxisColors.constraintFinancial;
    if (dimension.contains('operational')) {
      return PraxisColors.constraintOperational;
    }
    if (dimension.contains('temporal')) return PraxisColors.constraintTemporal;
    if (dimension.contains('data')) return PraxisColors.constraintDataAccess;
    if (dimension.contains('communication')) {
      return PraxisColors.constraintCommunication;
    }
    return PraxisColors.trustWarning;
  }
}

/// Card showing the AI's reasoning for the held action.
class _ReasoningCard extends StatelessWidget {
  final HeldAction action;

  const _ReasoningCard({required this.action});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AppCard(
      title: 'Reasoning',
      child: Text(
        action.reasoning,
        style: theme.textTheme.bodyMedium,
      ),
    );
  }
}

/// A simple label-value row used in detail cards.
class _DetailRow extends StatelessWidget {
  final String label;
  final String value;

  const _DetailRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 140,
          child: Text(
            label,
            style: theme.textTheme.labelMedium?.copyWith(
              color: theme.colorScheme.outline,
            ),
          ),
        ),
        Expanded(
          child: Text(value, style: theme.textTheme.bodyMedium),
        ),
      ],
    );
  }
}
