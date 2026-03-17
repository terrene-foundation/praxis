import 'package:flutter/material.dart';

import '../colors.dart';
import '../spacing.dart';

/// A horizontal bar gauge for displaying constraint usage.
class ConstraintGauge extends StatelessWidget {
  final String label;
  final double value; // 0.0 to 1.0
  final Color? color;
  final String? valueLabel;

  const ConstraintGauge({
    super.key,
    required this.label,
    required this.value,
    this.color,
    this.valueLabel,
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
            if (valueLabel != null)
              Text(
                valueLabel!,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.outline,
                ),
              ),
          ],
        ),
        const SizedBox(height: PraxisSpacing.xs),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: value.clamp(0.0, 1.0),
            backgroundColor: effectiveColor.withValues(alpha: 0.15),
            valueColor: AlwaysStoppedAnimation<Color>(effectiveColor),
            minHeight: 8,
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

/// A compact five-dimension constraint summary using colored dots.
class ConstraintDotsIndicator extends StatelessWidget {
  /// Usage values for each dimension: [financial, operational, temporal, dataAccess, communication].
  final List<double> values;

  const ConstraintDotsIndicator({super.key, required this.values});

  @override
  Widget build(BuildContext context) {
    const colors = [
      PraxisColors.constraintFinancial,
      PraxisColors.constraintOperational,
      PraxisColors.constraintTemporal,
      PraxisColors.constraintDataAccess,
      PraxisColors.constraintCommunication,
    ];
    const labels = ['Financial', 'Operational', 'Temporal', 'Data Access', 'Communication'];

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(5, (i) {
        final v = i < values.length ? values[i] : 0.0;
        return Padding(
          padding: const EdgeInsets.only(right: 4),
          child: Tooltip(
            message: '${labels[i]}: ${(v * 100).toInt()}%',
            child: Container(
              width: 10,
              height: 10,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: _dotColor(v, colors[i]),
              ),
            ),
          ),
        );
      }),
    );
  }

  Color _dotColor(double v, Color baseColor) {
    if (v <= 0.5) return baseColor;
    if (v <= 0.75) return PraxisColors.trustCaution;
    if (v <= 0.9) return PraxisColors.trustWarning;
    return PraxisColors.trustViolation;
  }
}
