import 'package:flutter/material.dart';

import '../colors.dart';
import '../spacing.dart';

/// A horizontal bar gauge for displaying constraint usage on mobile.
class ConstraintGauge extends StatelessWidget {
  final String label;
  final double value;
  final Color? color;

  const ConstraintGauge({
    super.key,
    required this.label,
    required this.value,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final effectiveColor = color ?? _colorForValue(value);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: theme.textTheme.labelMedium),
            Text(
              '${(value * 100).toInt()}%',
              style: theme.textTheme.labelSmall,
            ),
          ],
        ),
        const SizedBox(height: MobileSpacing.xs),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: value.clamp(0.0, 1.0),
            backgroundColor: effectiveColor.withValues(alpha: 0.15),
            valueColor: AlwaysStoppedAnimation<Color>(effectiveColor),
            minHeight: 6,
          ),
        ),
      ],
    );
  }

  Color _colorForValue(double v) {
    if (v <= 0.5) return PraxisColors.trustHealthy;
    if (v <= 0.75) return PraxisColors.trustCaution;
    if (v <= 0.9) return PraxisColors.trustWarning;
    return PraxisColors.trustViolation;
  }
}
