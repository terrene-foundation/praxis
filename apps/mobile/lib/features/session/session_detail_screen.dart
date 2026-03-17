import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';

/// Detail screen for a single session on mobile.
///
/// Shows constraint summary, session metadata, and deliberation timeline
/// in a single-column layout optimized for mobile screens.
class SessionDetailScreen extends ConsumerWidget {
  final String sessionId;

  const SessionDetailScreen({super.key, required this.sessionId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(sessionProvider(sessionId));

    return Scaffold(
      appBar: AppBar(
        title: session.maybeWhen(
          data: (s) => Text(s.name),
          orElse: () => const Text('Session'),
        ),
      ),
      body: session.when(
        data: (s) => _SessionDetailBody(session: s, sessionId: sessionId),
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
              Padding(
                padding: MobileSpacing.pagePadding,
                child: Text(
                  'Failed to load session: $e',
                  textAlign: TextAlign.center,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Main body content (scrollable)
// ---------------------------------------------------------------------------

class _SessionDetailBody extends StatelessWidget {
  final Session session;
  final String sessionId;

  const _SessionDetailBody({
    required this.session,
    required this.sessionId,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return SingleChildScrollView(
      padding: MobileSpacing.pagePadding,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Status row
          Row(
            children: [
              Expanded(
                child: Text(session.domain.toUpperCase(),
                    style: theme.textTheme.bodyMedium),
              ),
              SessionStatusBadge(status: session.status),
            ],
          ),
          const SizedBox(height: MobileSpacing.lg),

          // Constraint summary: horizontal scroll of 5 cards
          Text('Constraints', style: theme.textTheme.titleSmall),
          const SizedBox(height: MobileSpacing.sm),
          _ConstraintSummaryScroll(constraints: session.constraints),
          const SizedBox(height: MobileSpacing.lg),

          // Session metadata
          _SessionMetadataCard(session: session),
          const SizedBox(height: MobileSpacing.lg),

          // Deliberation timeline
          Text('Deliberation Timeline', style: theme.textTheme.titleSmall),
          const SizedBox(height: MobileSpacing.sm),
          _DeliberationTimeline(sessionId: sessionId),

          // Bottom safe area padding
          const SizedBox(height: MobileSpacing.xl),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Constraint summary: horizontal scroll of small cards
// ---------------------------------------------------------------------------

class _ConstraintSummaryScroll extends StatelessWidget {
  final ConstraintSet constraints;

  const _ConstraintSummaryScroll({required this.constraints});

  @override
  Widget build(BuildContext context) {
    final dimensions = _extractDimensions(constraints);

    return SizedBox(
      height: 88,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: dimensions.length,
        separatorBuilder: (_, __) => const SizedBox(width: MobileSpacing.sm),
        itemBuilder: (context, index) {
          final d = dimensions[index];
          return _ConstraintMiniCard(dimension: d);
        },
      ),
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
        name: 'Comms',
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

class _ConstraintMiniCard extends StatelessWidget {
  final _DimensionData dimension;

  const _ConstraintMiniCard({required this.dimension});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final percentage = (dimension.utilization * 100).toInt();

    return SizedBox(
      width: 120,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(MobileSpacing.sm),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                dimension.name,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.outline,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: MobileSpacing.xs),
              Text(
                '$percentage%',
                style: theme.textTheme.titleLarge?.copyWith(
                  color: dimension.color,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: MobileSpacing.xs),
              ClipRRect(
                borderRadius: BorderRadius.circular(3),
                child: LinearProgressIndicator(
                  value: dimension.utilization,
                  backgroundColor:
                      dimension.color.withValues(alpha: 0.15),
                  valueColor:
                      AlwaysStoppedAnimation<Color>(dimension.color),
                  minHeight: 4,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Session metadata card (compact)
// ---------------------------------------------------------------------------

class _SessionMetadataCard extends StatelessWidget {
  final Session session;

  const _SessionMetadataCard({required this.session});

  @override
  Widget build(BuildContext context) {
    return AppCard(
      title: 'Session Info',
      child: Column(
        children: [
          _InfoRow(
            icon: Icons.tag,
            label: 'ID',
            value: _truncateId(session.id),
          ),
          const SizedBox(height: MobileSpacing.sm),
          _InfoRow(
            icon: Icons.person_outline,
            label: 'Created by',
            value: session.createdBy,
          ),
          const SizedBox(height: MobileSpacing.sm),
          _InfoRow(
            icon: Icons.access_time,
            label: 'Created',
            value: _formatTimestamp(session.createdAt),
          ),
          if (session.endedAt != null) ...[
            const SizedBox(height: MobileSpacing.sm),
            _InfoRow(
              icon: Icons.stop_circle_outlined,
              label: 'Ended',
              value: _formatTimestamp(session.endedAt!),
            ),
          ],
          if (session.workspaceId != null) ...[
            const SizedBox(height: MobileSpacing.sm),
            _InfoRow(
              icon: Icons.workspaces_outline,
              label: 'Workspace',
              value: session.workspaceId!,
            ),
          ],
          if (session.description != null &&
              session.description!.isNotEmpty) ...[
            const SizedBox(height: MobileSpacing.sm),
            _InfoRow(
              icon: Icons.notes,
              label: 'Description',
              value: session.description!,
            ),
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

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 18, color: Colors.grey),
        const SizedBox(width: MobileSpacing.sm),
        SizedBox(
          width: 80,
          child: Text(
            label,
            style: theme.textTheme.labelSmall?.copyWith(
              color: Colors.grey,
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
// Deliberation timeline (embedded list, not scrollable -- parent scrolls)
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
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: MobileSpacing.lg),
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.timeline, size: 40, color: Colors.grey.shade400),
                  const SizedBox(height: MobileSpacing.sm),
                  Text(
                    'No deliberation records yet.',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Colors.grey,
                        ),
                  ),
                ],
              ),
            ),
          );
        }

        // Use a non-scrollable column since the parent is a SingleChildScrollView.
        return Column(
          children: records.map((record) {
            return _MobileTimelineEntry(record: record);
          }).toList(),
        );
      },
      loading: () => const AppLoading(count: 3),
      error: (e, _) => Padding(
        padding: const EdgeInsets.symmetric(vertical: MobileSpacing.lg),
        child: Center(child: Text('Failed to load timeline: $e')),
      ),
    );
  }
}

class _MobileTimelineEntry extends StatelessWidget {
  final DeliberationRecord record;

  const _MobileTimelineEntry({required this.record});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.only(bottom: MobileSpacing.sm),
      child: AppCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header: type badge + timestamp
            Row(
              children: [
                _TypeBadge(type: record.type),
                const Spacer(),
                Text(
                  _formatTime(record.createdAt),
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: Colors.grey,
                  ),
                ),
              ],
            ),
            const SizedBox(height: MobileSpacing.sm),

            // Summary
            Text(
              record.summary,
              style: theme.textTheme.bodyMedium,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: MobileSpacing.xs),

            // Reasoning preview
            Text(
              record.reasoning,
              style: theme.textTheme.bodySmall?.copyWith(
                color: Colors.grey,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: MobileSpacing.xs),

            // Actor
            Text(
              record.principalName,
              style: theme.textTheme.labelSmall?.copyWith(
                color: Colors.grey,
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatTime(DateTime dt) {
    final local = dt.toLocal();
    return '${local.month.toString().padLeft(2, '0')}/'
        '${local.day.toString().padLeft(2, '0')} '
        '${local.hour.toString().padLeft(2, '0')}:'
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
