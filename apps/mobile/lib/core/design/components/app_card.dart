import 'package:flutter/material.dart';

import '../spacing.dart';

/// A mobile-optimized card component with larger border radius and touch-friendly sizing.
class AppCard extends StatelessWidget {
  final Widget child;
  final String? title;
  final VoidCallback? onTap;
  final EdgeInsetsGeometry? padding;

  const AppCard({
    super.key,
    required this.child,
    this.title,
    this.onTap,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final effectivePadding = padding ?? MobileSpacing.cardPadding;

    Widget content = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (title != null)
          Padding(
            padding: effectivePadding,
            child: Text(title!, style: theme.textTheme.titleMedium),
          ),
        if (title != null) const Divider(height: 1),
        Padding(padding: effectivePadding, child: child),
      ],
    );

    if (onTap != null) {
      return Card(
        clipBehavior: Clip.antiAlias,
        child: InkWell(onTap: onTap, child: content),
      );
    }

    return Card(child: content);
  }
}
