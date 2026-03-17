import 'package:flutter/material.dart';
import 'package:praxis_shared/praxis_shared.dart';

import 'app_badge.dart';

/// A badge displaying session status with appropriate color.
class SessionStatusBadge extends StatelessWidget {
  final SessionStatus status;

  const SessionStatusBadge({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    final (label, variant) = switch (status) {
      SessionStatus.active => ('Active', AppBadgeVariant.success),
      SessionStatus.paused => ('Paused', AppBadgeVariant.warning),
      SessionStatus.ended => ('Ended', AppBadgeVariant.neutral),
    };
    return AppBadge(text: label, variant: variant);
  }
}

/// A badge displaying constraint health level.
class ConstraintHealthBadge extends StatelessWidget {
  final String level; // healthy, caution, warning, violation, held
  final String? label;

  const ConstraintHealthBadge({
    super.key,
    required this.level,
    this.label,
  });

  @override
  Widget build(BuildContext context) {
    final (text, variant) = switch (level) {
      'healthy' => (label ?? 'Healthy', AppBadgeVariant.success),
      'caution' => (label ?? 'Caution', AppBadgeVariant.warning),
      'warning' => (label ?? 'Warning', AppBadgeVariant.warning),
      'violation' => (label ?? 'Violation', AppBadgeVariant.error),
      'held' => (label ?? 'Held', AppBadgeVariant.info),
      _ => (label ?? level, AppBadgeVariant.neutral),
    };
    return AppBadge(text: text, variant: variant);
  }
}

/// A badge displaying held action status.
class HeldActionStatusBadge extends StatelessWidget {
  final HeldActionStatus status;

  const HeldActionStatusBadge({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    final (label, variant) = switch (status) {
      HeldActionStatus.pending => ('Pending', AppBadgeVariant.warning),
      HeldActionStatus.approved => ('Approved', AppBadgeVariant.success),
      HeldActionStatus.denied => ('Denied', AppBadgeVariant.error),
      HeldActionStatus.approvedWithConditions => (
          'Conditional',
          AppBadgeVariant.info,
        ),
      HeldActionStatus.expired => ('Expired', AppBadgeVariant.neutral),
    };
    return AppBadge(text: label, variant: variant);
  }
}
