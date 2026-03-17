import 'package:flutter/material.dart';

import '../spacing.dart';

/// Skeleton loader variants.
enum SkeletonVariant { card, listItem, paragraph }

/// A shimmer-style loading skeleton placeholder.
class AppLoading extends StatefulWidget {
  final SkeletonVariant variant;
  final int count;

  const AppLoading({
    super.key,
    this.variant = SkeletonVariant.card,
    this.count = 1,
  });

  @override
  State<AppLoading> createState() => _AppLoadingState();
}

class _AppLoadingState extends State<AppLoading>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return Column(
          children: List.generate(widget.count, (index) {
            return Padding(
              padding: const EdgeInsets.only(bottom: PraxisSpacing.sm),
              child: _buildSkeleton(context),
            );
          }),
        );
      },
    );
  }

  Widget _buildSkeleton(BuildContext context) {
    final shimmerColor = Theme.of(context).brightness == Brightness.light
        ? Colors.grey.shade200
        : Colors.grey.shade800;
    final highlightColor = Theme.of(context).brightness == Brightness.light
        ? Colors.grey.shade100
        : Colors.grey.shade700;
    final color = Color.lerp(shimmerColor, highlightColor, _controller.value)!;

    return switch (widget.variant) {
      SkeletonVariant.card => Container(
          height: 120,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      SkeletonVariant.listItem => Container(
          height: 56,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(8),
          ),
        ),
      SkeletonVariant.paragraph => Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(height: 14, width: double.infinity, color: color),
            const SizedBox(height: 8),
            Container(height: 14, width: 200, color: color),
            const SizedBox(height: 8),
            Container(height: 14, width: 260, color: color),
          ],
        ),
    };
  }
}
