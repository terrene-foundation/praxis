import 'package:flutter/material.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../colors.dart';

/// A small icon indicating trust verification status.
class TrustIndicator extends StatelessWidget {
  final VerificationStatus status;
  final double size;

  const TrustIndicator({
    super.key,
    required this.status,
    this.size = 16,
  });

  @override
  Widget build(BuildContext context) {
    final (icon, color, tooltip) = switch (status) {
      VerificationStatus.verified => (
          Icons.verified,
          PraxisColors.trustHealthy,
          'Verified',
        ),
      VerificationStatus.unverified => (
          Icons.help_outline,
          Colors.grey,
          'Unverified',
        ),
      VerificationStatus.failed => (
          Icons.warning,
          PraxisColors.trustViolation,
          'Verification Failed',
        ),
    };

    return Tooltip(
      message: tooltip,
      child: Icon(icon, color: color, size: size),
    );
  }
}
