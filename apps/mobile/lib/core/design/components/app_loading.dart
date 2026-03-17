import 'package:flutter/material.dart';

import '../spacing.dart';

/// Skeleton loader for mobile screens.
class AppLoading extends StatefulWidget {
  final int count;

  const AppLoading({super.key, this.count = 3});

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
        final shimmer = Theme.of(context).brightness == Brightness.light
            ? Colors.grey.shade200
            : Colors.grey.shade800;
        final highlight = Theme.of(context).brightness == Brightness.light
            ? Colors.grey.shade100
            : Colors.grey.shade700;
        final color = Color.lerp(shimmer, highlight, _controller.value)!;

        return Column(
          children: List.generate(widget.count, (index) {
            return Padding(
              padding: const EdgeInsets.only(bottom: MobileSpacing.sm),
              child: Container(
                height: 64,
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            );
          }),
        );
      },
    );
  }
}
