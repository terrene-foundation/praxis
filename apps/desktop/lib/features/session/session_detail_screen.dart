import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';

/// Detail screen for a single CO session.
///
/// Shows constraint summary, session metadata, and deliberation timeline.
class SessionDetailScreen extends ConsumerWidget {
  final String sessionId;

  const SessionDetailScreen({super.key, required this.sessionId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final session = ref.watch(sessionProvider(sessionId));

    return Scaffold(
      body: Padding(
        padding: PraxisSpacing.pagePadding,
        child: session.when(
          data: (s) => Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                children: [
                  Expanded(
                    child: Text(s.name, style: theme.textTheme.headlineMedium),
                  ),
                  SessionStatusBadge(status: s.status),
                ],
              ),
              const SizedBox(height: PraxisSpacing.lg),

              // Constraint summary row
              _ConstraintSummaryRow(constraints: s.constraints),
              const SizedBox(height: PraxisSpacing.lg),

              // Session metadata card
              _SessionMetadataCard(session: s),
              const SizedBox(height: PraxisSpacing.lg),

              // Deliberation timeline
              Text('Deliberation Timeline',
                  style: theme.textTheme.titleMedium),
              const SizedBox(height: PraxisSpacing.sm),
              Expanded(
                child: _DeliberationTimeline(sessionId: sessionId),
              ),
            ],
          ),
          loading: () =>
              const AppLoading(variant: SkeletonVariant.card, count: 3),
          error: (e, _) => Center(child: Text('Error: $e')),
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Constraint summary: row of 5 mini gauges
// ---------------------------------------------------------------------------

class _ConstraintSummaryRow extends StatelessWidget {
  final ConstraintSet constraints;

  const _ConstraintSummaryRow({required this.constraints});

  @override
  Widget build(BuildContext context) {
    final dimensions = _extractDimensions(constraints);

    return Row(
      children: dimensions.map((d) {
        return Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: PraxisSpacing.xs),
            child: ConstraintGauge(
              label: d.name,
              value: d.utilization,
              color: d.color,
              valueLabel: '${(d.utilization * 100).toInt()}%',
            ),
          ),
        );
      }).toList(),
    );
  }

  List<_DimensionData> _extractDimensions(ConstraintSet c) {
    return [
      _DimensionData(
        name: 'Financial',
        utilization: c.financial.maxAmount > 0
            ? (c.financial.currentUsage / c.financial.maxAmount).clamp(0.0, 1.0)
            : 0.0,
        color: PraxisColors.constraintFinancial,
      ),
      _DimensionData(
        name: 'Operational',
        // Operational has no numeric utilization; show based on how
        // restrictive it is (more blocked actions = higher utilization).
        utilization: c.operational.blockedActions.isNotEmpty
            ? (c.operational.blockedActions.length /
                    (c.operational.allowedActions.length +
                        c.operational.blockedActions.length))
                .clamp(0.0, 1.0)
            : 0.0,
        color: PraxisColors.constraintOperational,
      ),
      _DimensionData(
        name: 'Temporal',
        utilization: _temporalUtilization(c.temporal),
        color: PraxisColors.constraintTemporal,
      ),
      _DimensionData(
        name: 'Data Access',
        utilization: c.dataAccess.blockedResources.isNotEmpty
            ? (c.dataAccess.blockedResources.length /
                    (c.dataAccess.allowedResources.length +
                        c.dataAccess.blockedResources.length))
                .clamp(0.0, 1.0)
            : 0.0,
        color: PraxisColors.constraintDataAccess,
      ),
      _DimensionData(
        name: 'Communication',
        utilization: c.communication.blockedChannels.isNotEmpty
            ? (c.communication.blockedChannels.length /
                    (c.communication.allowedChannels.length +
                        c.communication.blockedChannels.length))
                .clamp(0.0, 1.0)
            : 0.0,
        color: PraxisColors.constraintCommunication,
      ),
    ];
  }

  double _temporalUtilization(TemporalConstraint t) {
    if (t.validUntil != null) {
      final total = t.validUntil!.difference(t.validFrom ?? DateTime.now());
      final elapsed = DateTime.now().difference(t.validFrom ?? DateTime.now());
      if (total.inMinutes > 0) {
        return (elapsed.inMinutes / total.inMinutes).clamp(0.0, 1.0);
      }
    }
    return 0.0;
  }
}

class _DimensionData {
  final String name;
  final double utilization;
  final Color color;

  const _DimensionData({
    required this.name,
    required this.utilization,
    required this.color,
  });
}

// ---------------------------------------------------------------------------
// Session metadata card
// ---------------------------------------------------------------------------

class _SessionMetadataCard extends StatelessWidget {
  final Session session;

  const _SessionMetadataCard({required this.session});

  @override
  Widget build(BuildContext context) {
    return AppCard(
      title: 'Session Information',
      child: Column(
        children: [
          _MetadataRow(label: 'Domain', value: session.domain.toUpperCase()),
          const SizedBox(height: PraxisSpacing.sm),
          _MetadataRow(label: 'Session ID', value: _truncateId(session.id)),
          const SizedBox(height: PraxisSpacing.sm),
          if (session.workspaceId != null) ...[
            _MetadataRow(label: 'Workspace', value: session.workspaceId!),
            const SizedBox(height: PraxisSpacing.sm),
          ],
          _MetadataRow(label: 'Created by', value: session.createdBy),
          const SizedBox(height: PraxisSpacing.sm),
          _MetadataRow(
            label: 'Created',
            value: _formatTimestamp(session.createdAt),
          ),
          if (session.endedAt != null) ...[
            const SizedBox(height: PraxisSpacing.sm),
            _MetadataRow(
              label: 'Ended',
              value: _formatTimestamp(session.endedAt!),
            ),
          ],
          if (session.description != null &&
              session.description!.isNotEmpty) ...[
            const SizedBox(height: PraxisSpacing.sm),
            _MetadataRow(label: 'Description', value: session.description!),
          ],
        ],
      ),
    );
  }

  String _truncateId(String id) {
    if (id.length <= 12) return id;
    return '${id.substring(0, 8)}...${id.substring(id.length - 4)}';
  }

  String _formatTimestamp(DateTime dt) {
    final local = dt.toLocal();
    return '${local.year}-${local.month.toString().padLeft(2, '0')}-'
        '${local.day.toString().padLeft(2, '0')} '
        '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }
}

class _MetadataRow extends StatelessWidget {
  final String label;
  final String value;

  const _MetadataRow({required this.label, required this.value});

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

// ---------------------------------------------------------------------------
// Deliberation timeline
// ---------------------------------------------------------------------------

class _DeliberationTimeline extends ConsumerWidget {
  final String sessionId;

  const _DeliberationTimeline({required this.sessionId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final timeline = ref.watch(sessionTimelineProvider(sessionId));

    return timeline.when(
      data: (records) {
        if (records.isEmpty) {
          return const AppEmptyState(
            icon: Icons.timeline,
            title: 'No deliberation records',
            description: 'Decisions and observations will appear here '
                'as the session progresses.',
          );
        }
        return ListView.separated(
          itemCount: records.length,
          separatorBuilder: (_, __) => const Divider(height: 1),
          itemBuilder: (context, index) {
            final record = records[index];
            return _TimelineEntry(record: record);
          },
        );
      },
      loading: () =>
          const AppLoading(variant: SkeletonVariant.listItem, count: 4),
      error: (e, _) => Center(child: Text('Failed to load timeline: $e')),
    );
  }
}

class _TimelineEntry extends StatelessWidget {
  final DeliberationRecord record;

  const _TimelineEntry({required this.record});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.symmetric(
        vertical: PraxisSpacing.sm,
        horizontal: PraxisSpacing.xs,
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Type badge
          SizedBox(
            width: 100,
            child: _TypeBadge(type: record.type),
          ),
          const SizedBox(width: PraxisSpacing.sm),

          // Content
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  record.summary,
                  style: theme.textTheme.bodyMedium,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  record.reasoning,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.outline,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          const SizedBox(width: PraxisSpacing.sm),

          // Timestamp and actor
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                _formatTime(record.createdAt),
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.outline,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                record.principalName,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.outline,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _formatTime(DateTime dt) {
    final local = dt.toLocal();
    return '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }
}

class _TypeBadge extends StatelessWidget {
  final DeliberationType type;

  const _TypeBadge({required this.type});

  @override
  Widget build(BuildContext context) {
    final (label, variant) = switch (type) {
      DeliberationType.decision => ('Decision', AppBadgeVariant.info),
      DeliberationType.observation => ('Observation', AppBadgeVariant.neutral),
      DeliberationType.question => ('Question', AppBadgeVariant.warning),
      DeliberationType.constraintChange => ('Constraint', AppBadgeVariant.error),
      DeliberationType.approval => ('Approval', AppBadgeVariant.success),
      DeliberationType.denial => ('Denial', AppBadgeVariant.error),
    };
    return AppBadge(text: label, variant: variant);
  }
}
