import 'package:flutter/material.dart';
import 'package:praxis_shared/praxis_shared.dart';

import 'app_badge.dart';

/// Session status badge for mobile.
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

/// Held action status badge for mobile.
class HeldActionStatusBadge extends StatelessWidget {
  final HeldActionStatus status;

  const HeldActionStatusBadge({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    final (label, variant) = switch (status) {
      HeldActionStatus.pending => ('Pending', AppBadgeVariant.warning),
      HeldActionStatus.approved => ('Approved', AppBadgeVariant.success),
      HeldActionStatus.denied => ('Denied', AppBadgeVariant.error),
      HeldActionStatus.approvedWithConditions => ('Conditional', AppBadgeVariant.info),
      HeldActionStatus.expired => ('Expired', AppBadgeVariant.neutral),
    };
    return AppBadge(text: label, variant: variant);
  }
}
