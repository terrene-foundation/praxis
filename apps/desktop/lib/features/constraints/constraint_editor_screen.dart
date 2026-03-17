import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';

/// Provider to load constraints for a given session.
final sessionConstraintsProvider =
    FutureProvider.family<ConstraintSet, String>((ref, sessionId) async {
  final client = ref.watch(praxisClientProvider);
  return client.constraints.get(sessionId);
});

/// Screen for editing the five CO constraint dimensions for a session.
///
/// Enforces tightening-only: sliders cannot exceed their original values.
/// Requires a rationale before saving.
class ConstraintEditorScreen extends ConsumerStatefulWidget {
  final String? sessionId;

  const ConstraintEditorScreen({super.key, this.sessionId});

  @override
  ConsumerState<ConstraintEditorScreen> createState() =>
      _ConstraintEditorScreenState();
}

class _ConstraintEditorScreenState
    extends ConsumerState<ConstraintEditorScreen> {
  // Financial
  double _maxSpend = 500;
  double _originalMaxSpend = 500;
  String _currency = 'USD';

  // Temporal
  int _maxDurationMinutes = 240;
  int _originalMaxDurationMinutes = 240;

  // Operational
  final Map<String, bool> _allowedActions = {
    'read': true,
    'write': true,
    'execute': false,
    'delete': false,
    'deploy': false,
  };

  // Data Access
  final List<String> _allowedPaths = [];
  final List<String> _blockedPaths = [];

  // Communication
  final Map<String, bool> _allowedChannels = {
    'internal': true,
    'email': false,
    'external': false,
  };

  // Rationale
  final _rationaleController = TextEditingController();

  bool _initialized = false;
  bool _isSaving = false;
  String? _saveError;
  bool _saveSuccess = false;

  @override
  void dispose() {
    _rationaleController.dispose();
    super.dispose();
  }

  void _initFromConstraintSet(ConstraintSet cs) {
    if (_initialized) return;
    _initialized = true;

    _maxSpend = cs.financial.maxAmount;
    _originalMaxSpend = cs.financial.maxAmount;
    _currency = cs.financial.currency;

    _maxDurationMinutes = cs.temporal.maxDurationMinutes ?? 240;
    _originalMaxDurationMinutes = cs.temporal.maxDurationMinutes ?? 240;

    for (final action in cs.operational.allowedActions) {
      _allowedActions[action] = true;
    }
    for (final action in cs.operational.blockedActions) {
      _allowedActions[action] = false;
    }

    _allowedPaths
      ..clear()
      ..addAll(cs.dataAccess.allowedResources);
    _blockedPaths
      ..clear()
      ..addAll(cs.dataAccess.blockedResources);

    for (final channel in cs.communication.allowedChannels) {
      _allowedChannels[channel] = true;
    }
    for (final channel in cs.communication.blockedChannels) {
      _allowedChannels[channel] = false;
    }
  }

  ConstraintSet _buildConstraintSet() {
    final allowed = _allowedActions.entries
        .where((e) => e.value)
        .map((e) => e.key)
        .toList();
    final blocked = _allowedActions.entries
        .where((e) => !e.value)
        .map((e) => e.key)
        .toList();
    final allowedCh = _allowedChannels.entries
        .where((e) => e.value)
        .map((e) => e.key)
        .toList();
    final blockedCh = _allowedChannels.entries
        .where((e) => !e.value)
        .map((e) => e.key)
        .toList();

    return ConstraintSet(
      financial: FinancialConstraint(
        maxAmount: _maxSpend,
        currentUsage: 0,
        currency: _currency,
      ),
      operational: OperationalConstraint(
        allowedActions: allowed,
        blockedActions: blocked,
      ),
      temporal: TemporalConstraint(
        maxDurationMinutes: _maxDurationMinutes,
      ),
      dataAccess: DataAccessConstraint(
        allowedResources: _allowedPaths,
        blockedResources: _blockedPaths,
      ),
      communication: CommunicationConstraint(
        allowedChannels: allowedCh,
        blockedChannels: blockedCh,
      ),
    );
  }

  Future<void> _save() async {
    if (widget.sessionId == null) return;
    final rationale = _rationaleController.text.trim();
    if (rationale.isEmpty) {
      setState(() => _saveError = 'A rationale is required.');
      return;
    }

    setState(() {
      _isSaving = true;
      _saveError = null;
    });

    try {
      final client = ref.read(praxisClientProvider);
      await client.constraints.update(widget.sessionId!, _buildConstraintSet());
      ref.invalidate(sessionConstraintsProvider(widget.sessionId!));
      if (mounted) {
        setState(() {
          _isSaving = false;
          _saveSuccess = true;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isSaving = false;
          _saveError = e is PraxisApiException
              ? e.userMessage
              : 'Failed to save constraints.';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasSession = widget.sessionId != null;

    return Scaffold(
      body: Padding(
        padding: PraxisSpacing.pagePadding,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              hasSession ? 'Session Constraints' : 'Constraint Templates',
              style: theme.textTheme.headlineMedium,
            ),
            const SizedBox(height: PraxisSpacing.lg),
            Expanded(
              child: hasSession
                  ? _buildSessionEditor(theme)
                  : const AppEmptyState(
                      icon: Icons.tune,
                      title: 'No session selected',
                      description:
                          'Open a session to edit its constraints, or browse constraint presets from the sessions view.',
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSessionEditor(ThemeData theme) {
    final constraintsAsync =
        ref.watch(sessionConstraintsProvider(widget.sessionId!));

    return constraintsAsync.when(
      data: (cs) {
        _initFromConstraintSet(cs);
        return _buildEditorForm(theme);
      },
      loading: () => const AppLoading(variant: SkeletonVariant.card, count: 3),
      error: (e, _) => AppEmptyState(
        icon: Icons.error_outline,
        title: 'Failed to load constraints',
        description: e is PraxisApiException
            ? e.userMessage
            : 'Could not reach the server.',
        actionLabel: 'Retry',
        onAction: () =>
            ref.invalidate(sessionConstraintsProvider(widget.sessionId!)),
      ),
    );
  }

  Widget _buildEditorForm(ThemeData theme) {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _FinancialSection(
            maxSpend: _maxSpend,
            originalMax: _originalMaxSpend,
            currency: _currency,
            onChanged: (v) => setState(() => _maxSpend = v),
          ),
          const SizedBox(height: PraxisSpacing.lg),
          _TemporalSection(
            maxDuration: _maxDurationMinutes,
            originalMax: _originalMaxDurationMinutes,
            onChanged: (v) => setState(() => _maxDurationMinutes = v),
          ),
          const SizedBox(height: PraxisSpacing.lg),
          _OperationalSection(
            actions: _allowedActions,
            onChanged: (key, val) =>
                setState(() => _allowedActions[key] = val),
          ),
          const SizedBox(height: PraxisSpacing.lg),
          _DataAccessSection(
            allowedPaths: _allowedPaths,
            blockedPaths: _blockedPaths,
            onAllowedAdded: (p) => setState(() => _allowedPaths.add(p)),
            onAllowedRemoved: (p) => setState(() => _allowedPaths.remove(p)),
            onBlockedAdded: (p) => setState(() => _blockedPaths.add(p)),
            onBlockedRemoved: (p) => setState(() => _blockedPaths.remove(p)),
          ),
          const SizedBox(height: PraxisSpacing.lg),
          _CommunicationSection(
            channels: _allowedChannels,
            onChanged: (key, val) =>
                setState(() => _allowedChannels[key] = val),
          ),
          const SizedBox(height: PraxisSpacing.xl),
          _buildRationaleAndSave(theme),
          const SizedBox(height: PraxisSpacing.xl),
        ],
      ),
    );
  }

  Widget _buildRationaleAndSave(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppCard(
          title: 'Rationale (required)',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Explain why you are changing these constraints. This is captured in the deliberation log.',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.outline,
                ),
              ),
              const SizedBox(height: PraxisSpacing.sm),
              AppInput(
                hint: 'e.g. "Tightening financial limit after phase 1 completion"',
                controller: _rationaleController,
                maxLines: 3,
                enabled: !_isSaving,
              ),
            ],
          ),
        ),
        const SizedBox(height: PraxisSpacing.md),
        if (_saveError != null) ...[
          Container(
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
                    _saveError!,
                    style: TextStyle(
                      color: theme.colorScheme.onErrorContainer,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: PraxisSpacing.md),
        ],
        if (_saveSuccess) ...[
          Container(
            padding: PraxisSpacing.cardPadding,
            decoration: BoxDecoration(
              color: Colors.green.shade50,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Row(
              children: [
                Icon(Icons.check_circle, color: PraxisColors.trustHealthy),
                SizedBox(width: PraxisSpacing.sm),
                Text('Constraints saved successfully.'),
              ],
            ),
          ),
          const SizedBox(height: PraxisSpacing.md),
        ],
        AppButton(
          label: 'Save Constraints',
          icon: Icons.save,
          size: AppButtonSize.large,
          isLoading: _isSaving,
          onPressed: _isSaving ? null : _save,
        ),
      ],
    );
  }
}

// ---------------------------------------------------------------------------
// Section widgets — one per constraint dimension
// ---------------------------------------------------------------------------

/// Financial constraint: slider for max spend.
class _FinancialSection extends StatelessWidget {
  final double maxSpend;
  final double originalMax;
  final String currency;
  final ValueChanged<double> onChanged;

  const _FinancialSection({
    required this.maxSpend,
    required this.originalMax,
    required this.currency,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AppCard(
      title: 'Financial',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.attach_money,
                  color: PraxisColors.constraintFinancial, size: 20),
              const SizedBox(width: PraxisSpacing.xs),
              Text(
                'Maximum spend: ${maxSpend.toStringAsFixed(0)} $currency',
                style: theme.textTheme.bodyMedium,
              ),
            ],
          ),
          const SizedBox(height: PraxisSpacing.sm),
          Slider(
            value: maxSpend,
            min: 0,
            max: originalMax,
            divisions: (originalMax / 10).round().clamp(1, 100),
            label: '${maxSpend.toStringAsFixed(0)} $currency',
            onChanged: onChanged,
          ),
          Text(
            'Cannot exceed the original limit of ${originalMax.toStringAsFixed(0)} $currency (tightening-only).',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.outline,
            ),
          ),
        ],
      ),
    );
  }
}

/// Temporal constraint: slider for max duration in minutes.
class _TemporalSection extends StatelessWidget {
  final int maxDuration;
  final int originalMax;
  final ValueChanged<int> onChanged;

  const _TemporalSection({
    required this.maxDuration,
    required this.originalMax,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hours = maxDuration ~/ 60;
    final mins = maxDuration % 60;
    final display =
        hours > 0 ? '${hours}h ${mins}m' : '${mins}m';

    return AppCard(
      title: 'Temporal',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.schedule,
                  color: PraxisColors.constraintTemporal, size: 20),
              const SizedBox(width: PraxisSpacing.xs),
              Text(
                'Maximum duration: $display',
                style: theme.textTheme.bodyMedium,
              ),
            ],
          ),
          const SizedBox(height: PraxisSpacing.sm),
          Slider(
            value: maxDuration.toDouble(),
            min: 0,
            max: originalMax.toDouble(),
            divisions: (originalMax ~/ 15).clamp(1, 32),
            label: display,
            onChanged: (v) => onChanged(v.round()),
          ),
          Text(
            'Cannot exceed the original limit of ${originalMax ~/ 60}h ${originalMax % 60}m.',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.outline,
            ),
          ),
        ],
      ),
    );
  }
}

/// Operational constraint: checkboxes for allowed actions.
class _OperationalSection extends StatelessWidget {
  final Map<String, bool> actions;
  final void Function(String, bool) onChanged;

  const _OperationalSection({
    required this.actions,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return AppCard(
      title: 'Operational',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.engineering,
                  color: PraxisColors.constraintOperational, size: 20),
              const SizedBox(width: PraxisSpacing.xs),
              Text(
                'Allowed actions',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
          ),
          const SizedBox(height: PraxisSpacing.sm),
          Wrap(
            spacing: PraxisSpacing.sm,
            children: actions.entries.map((entry) {
              return FilterChip(
                label: Text(_capitalize(entry.key)),
                selected: entry.value,
                onSelected: (val) => onChanged(entry.key, val),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  String _capitalize(String s) =>
      s.isEmpty ? s : '${s[0].toUpperCase()}${s.substring(1)}';
}

/// Data Access constraint: add/remove allowed and blocked paths.
class _DataAccessSection extends StatelessWidget {
  final List<String> allowedPaths;
  final List<String> blockedPaths;
  final ValueChanged<String> onAllowedAdded;
  final ValueChanged<String> onAllowedRemoved;
  final ValueChanged<String> onBlockedAdded;
  final ValueChanged<String> onBlockedRemoved;

  const _DataAccessSection({
    required this.allowedPaths,
    required this.blockedPaths,
    required this.onAllowedAdded,
    required this.onAllowedRemoved,
    required this.onBlockedAdded,
    required this.onBlockedRemoved,
  });

  @override
  Widget build(BuildContext context) {
    return AppCard(
      title: 'Data Access',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.folder_open,
                  color: PraxisColors.constraintDataAccess, size: 20),
              const SizedBox(width: PraxisSpacing.xs),
              Text(
                'Resource paths',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
          ),
          const SizedBox(height: PraxisSpacing.md),
          _PathList(
            label: 'Allowed',
            paths: allowedPaths,
            onAdd: onAllowedAdded,
            onRemove: onAllowedRemoved,
            chipColor: Colors.green,
          ),
          const SizedBox(height: PraxisSpacing.md),
          _PathList(
            label: 'Blocked',
            paths: blockedPaths,
            onAdd: onBlockedAdded,
            onRemove: onBlockedRemoved,
            chipColor: Colors.red,
          ),
        ],
      ),
    );
  }
}

/// Editable path list with add/remove.
class _PathList extends StatefulWidget {
  final String label;
  final List<String> paths;
  final ValueChanged<String> onAdd;
  final ValueChanged<String> onRemove;
  final Color chipColor;

  const _PathList({
    required this.label,
    required this.paths,
    required this.onAdd,
    required this.onRemove,
    required this.chipColor,
  });

  @override
  State<_PathList> createState() => _PathListState();
}

class _PathListState extends State<_PathList> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _add() {
    final text = _controller.text.trim();
    if (text.isNotEmpty) {
      widget.onAdd(text);
      _controller.clear();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(widget.label, style: theme.textTheme.labelMedium),
        const SizedBox(height: PraxisSpacing.xs),
        Wrap(
          spacing: PraxisSpacing.xs,
          runSpacing: PraxisSpacing.xs,
          children: widget.paths.map((p) {
            return Chip(
              label: Text(p, style: const TextStyle(fontSize: 12)),
              deleteIcon: const Icon(Icons.close, size: 16),
              onDeleted: () => widget.onRemove(p),
              backgroundColor: widget.chipColor.withValues(alpha: 0.1),
            );
          }).toList(),
        ),
        const SizedBox(height: PraxisSpacing.sm),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _controller,
                style: const TextStyle(fontSize: 13),
                decoration: InputDecoration(
                  hintText: 'Add path...',
                  isDense: true,
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 10,
                  ),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                onSubmitted: (_) => _add(),
              ),
            ),
            const SizedBox(width: PraxisSpacing.sm),
            IconButton(
              icon: const Icon(Icons.add_circle_outline),
              onPressed: _add,
              tooltip: 'Add',
            ),
          ],
        ),
      ],
    );
  }
}

/// Communication constraint: checkboxes for allowed channels.
class _CommunicationSection extends StatelessWidget {
  final Map<String, bool> channels;
  final void Function(String, bool) onChanged;

  const _CommunicationSection({
    required this.channels,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return AppCard(
      title: 'Communication',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.chat_outlined,
                  color: PraxisColors.constraintCommunication, size: 20),
              const SizedBox(width: PraxisSpacing.xs),
              Text(
                'Allowed channels',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
          ),
          const SizedBox(height: PraxisSpacing.sm),
          Wrap(
            spacing: PraxisSpacing.sm,
            children: channels.entries.map((entry) {
              return FilterChip(
                label: Text(_capitalize(entry.key)),
                selected: entry.value,
                onSelected: (val) => onChanged(entry.key, val),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  String _capitalize(String s) =>
      s.isEmpty ? s : '${s[0].toUpperCase()}${s.substring(1)}';
}
