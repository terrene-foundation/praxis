import 'package:flutter/material.dart';

import '../spacing.dart';

/// Elevation level for [AppCard].
enum AppCardElevation { flat, raised, floating }

/// A standardized card component with consistent border radius, background,
/// optional header, and tap interaction.
class AppCard extends StatelessWidget {
  final Widget child;
  final String? title;
  final List<Widget>? actions;
  final VoidCallback? onTap;
  final AppCardElevation elevation;
  final EdgeInsetsGeometry? padding;

  const AppCard({
    super.key,
    required this.child,
    this.title,
    this.actions,
    this.onTap,
    this.elevation = AppCardElevation.flat,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final effectivePadding = padding ?? PraxisSpacing.cardPadding;

    Widget content = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (title != null || (actions != null && actions!.isNotEmpty))
          Padding(
            padding: effectivePadding,
            child: Row(
              children: [
                if (title != null)
                  Expanded(
                    child: Text(
                      title!,
                      style: theme.textTheme.titleMedium,
                    ),
                  ),
                if (actions != null) ...actions!,
              ],
            ),
          ),
        if (title != null) const Divider(height: 1),
        Padding(
          padding: effectivePadding,
          child: child,
        ),
      ],
    );

    final double cardElevation;
    switch (elevation) {
      case AppCardElevation.flat:
        cardElevation = 0;
      case AppCardElevation.raised:
        cardElevation = 2;
      case AppCardElevation.floating:
        cardElevation = 8;
    }

    if (onTap != null) {
      return Card(
        elevation: cardElevation,
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: content,
        ),
      );
    }

    return Card(
      elevation: cardElevation,
      child: content,
    );
  }
}
