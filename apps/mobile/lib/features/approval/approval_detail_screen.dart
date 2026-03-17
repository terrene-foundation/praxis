import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';

/// Provider to fetch a single held action by ID from the pending list.
final _heldActionProvider =
    FutureProvider.family<HeldAction?, String>((ref, id) async {
  final approvals = await ref.watch(pendingApprovalsProvider.future);
  try {
    return approvals.firstWhere((a) => a.id == id);
  } catch (_) {
    return null;
  }
});

/// Detail screen for a held action on mobile.
///
/// Shows full action details with approve/deny buttons at the bottom.
/// Provides haptic feedback on user interaction and navigates back on success.
class ApprovalDetailScreen extends ConsumerStatefulWidget {
  final String approvalId;

  const ApprovalDetailScreen({super.key, required this.approvalId});

  @override
  ConsumerState<ApprovalDetailScreen> createState() =>
      _ApprovalDetailScreenState();
}

class _ApprovalDetailScreenState extends ConsumerState<ApprovalDetailScreen> {
  bool _isLoading = false;

  Future<void> _handleApprove(HeldAction action) async {
    HapticFeedback.mediumImpact();
    setState(() {
      _isLoading = true;
    });

    try {
      final client = ref.read(praxisClientProvider);
      await client.approvals.approve(action.sessionId, action.id);
      ref.invalidate(pendingApprovalsProvider);
      if (mounted) {
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to approve: $e'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    }
  }

  Future<void> _handleDeny(HeldAction action) async {
    HapticFeedback.mediumImpact();
    setState(() {
      _isLoading = true;
    });

    try {
      final client = ref.read(praxisClientProvider);
      await client.approvals.deny(action.sessionId, action.id);
      ref.invalidate(pendingApprovalsProvider);
      if (mounted) {
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to deny: $e'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final actionAsync = ref.watch(_heldActionProvider(widget.approvalId));
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Approval Detail')),
      body: actionAsync.when(
        data: (action) {
          if (action == null) {
            return const Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.search_off, size: 48, color: Colors.grey),
                  SizedBox(height: MobileSpacing.md),
                  Text('Held action not found.'),
                ],
              ),
            );
          }

          final isPending = action.status == HeldActionStatus.pending;

          return Column(
            children: [
              // Scrollable detail content
              Expanded(
                child: SingleChildScrollView(
                  padding: MobileSpacing.pagePadding,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Status badge
                      Row(
                        children: [
                          const Spacer(),
                          HeldActionStatusBadge(status: action.status),
                        ],
                      ),
                      const SizedBox(height: MobileSpacing.md),

                      // Action type
                      _DetailSection(
                        label: 'Action',
                        value: action.actionType,
                        icon: Icons.play_arrow,
                      ),
                      const SizedBox(height: MobileSpacing.md),

                      // Description / Resource
                      _DetailSection(
                        label: 'Resource',
                        value: action.description,
                        icon: Icons.folder_outlined,
                      ),
                      const SizedBox(height: MobileSpacing.md),

                      // Constraint dimension
                      _DetailSection(
                        label: 'Dimension',
                        value: action.constraintTriggered,
                        icon: Icons.tune,
                      ),
                      const SizedBox(height: MobileSpacing.lg),

                      // Reason / Reasoning
                      AppCard(
                        title: 'Reason',
                        child: Text(
                          action.reasoning,
                          style: theme.textTheme.bodyMedium,
                        ),
                      ),
                      const SizedBox(height: MobileSpacing.md),

                      // Timestamp
                      Text(
                        'Created: ${_formatTimestamp(action.createdAt)}',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: Colors.grey,
                        ),
                      ),
                      if (action.resolvedAt != null)
                        Padding(
                          padding:
                              const EdgeInsets.only(top: MobileSpacing.xs),
                          child: Text(
                            'Resolved: ${_formatTimestamp(action.resolvedAt!)}',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: Colors.grey,
                            ),
                          ),
                        ),
                      if (action.resolvedBy != null)
                        Padding(
                          padding:
                              const EdgeInsets.only(top: MobileSpacing.xs),
                          child: Text(
                            'Resolved by: ${action.resolvedBy}',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: Colors.grey,
                            ),
                          ),
                        ),

                      // Bottom padding for scrolling past buttons
                      const SizedBox(height: MobileSpacing.xl),
                    ],
                  ),
                ),
              ),

              // Action buttons at bottom
              if (isPending)
                SafeArea(
                  top: false,
                  child: Padding(
                    padding: const EdgeInsets.all(MobileSpacing.md),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // Approve button
                        SizedBox(
                          width: double.infinity,
                          height: MobileSpacing.minTouchTarget,
                          child: FilledButton(
                            onPressed: _isLoading
                                ? null
                                : () => _handleApprove(action),
                            style: FilledButton.styleFrom(
                              backgroundColor: PraxisColors.trustHealthy,
                              foregroundColor: Colors.white,
                            ),
                            child: _isLoading
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: Colors.white,
                                    ),
                                  )
                                : const Text(
                                    'Approve',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                          ),
                        ),
                        const SizedBox(height: MobileSpacing.sm),
                        // Deny button
                        SizedBox(
                          width: double.infinity,
                          height: MobileSpacing.minTouchTarget,
                          child: FilledButton(
                            onPressed: _isLoading
                                ? null
                                : () => _handleDeny(action),
                            style: FilledButton.styleFrom(
                              backgroundColor: PraxisColors.trustViolation,
                              foregroundColor: Colors.white,
                            ),
                            child: _isLoading
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: Colors.white,
                                    ),
                                  )
                                : const Text(
                                    'Deny',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          );
        },
        loading: () => const Padding(
          padding: MobileSpacing.pagePadding,
          child: AppLoading(count: 4),
        ),
        error: (e, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: MobileSpacing.md),
              Text('Error: $e'),
            ],
          ),
        ),
      ),
    );
  }

  String _formatTimestamp(DateTime dt) {
    final local = dt.toLocal();
    return '${local.year}-${local.month.toString().padLeft(2, '0')}-'
        '${local.day.toString().padLeft(2, '0')} '
        '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }
}

/// A labeled detail row with icon.
class _DetailSection extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;

  const _DetailSection({
    required this.label,
    required this.value,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 20, color: Colors.grey),
        const SizedBox(width: MobileSpacing.sm),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: Colors.grey,
                ),
              ),
              const SizedBox(height: 2),
              Text(value, style: theme.textTheme.bodyLarge),
            ],
          ),
        ),
      ],
    );
  }
}
