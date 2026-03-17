import 'package:flutter/material.dart';

/// Visual variant for [AppButton].
enum AppButtonVariant { primary, secondary, outlined, text, destructive }

/// Size preset for [AppButton].
enum AppButtonSize { small, medium, large }

/// A standardized button component with consistent sizing, loading state,
/// and variant styling.
class AppButton extends StatelessWidget {
  final String? label;
  final VoidCallback? onPressed;
  final AppButtonVariant variant;
  final AppButtonSize size;
  final bool isLoading;
  final IconData? icon;

  const AppButton({
    super.key,
    this.label,
    this.onPressed,
    this.variant = AppButtonVariant.primary,
    this.size = AppButtonSize.medium,
    this.isLoading = false,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final height = switch (size) {
      AppButtonSize.small => 32.0,
      AppButtonSize.medium => 40.0,
      AppButtonSize.large => 48.0,
    };

    final fontSize = switch (size) {
      AppButtonSize.small => 12.0,
      AppButtonSize.medium => 14.0,
      AppButtonSize.large => 16.0,
    };

    final effectiveOnPressed = isLoading ? null : onPressed;

    Widget child;
    if (isLoading) {
      child = SizedBox(
        width: fontSize + 2,
        height: fontSize + 2,
        child: const CircularProgressIndicator(strokeWidth: 2),
      );
    } else if (icon != null && label != null) {
      child = Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: fontSize + 4),
          const SizedBox(width: 8),
          Text(label!, style: TextStyle(fontSize: fontSize)),
        ],
      );
    } else if (icon != null) {
      child = Icon(icon, size: fontSize + 4);
    } else {
      child = Text(label ?? '', style: TextStyle(fontSize: fontSize));
    }

    final minSize = Size(icon != null && label == null ? height : 80, height);

    return switch (variant) {
      AppButtonVariant.primary => FilledButton(
          onPressed: effectiveOnPressed,
          style: FilledButton.styleFrom(minimumSize: minSize),
          child: child,
        ),
      AppButtonVariant.secondary => FilledButton.tonal(
          onPressed: effectiveOnPressed,
          style: FilledButton.styleFrom(minimumSize: minSize),
          child: child,
        ),
      AppButtonVariant.outlined => OutlinedButton(
          onPressed: effectiveOnPressed,
          style: OutlinedButton.styleFrom(minimumSize: minSize),
          child: child,
        ),
      AppButtonVariant.text => TextButton(
          onPressed: effectiveOnPressed,
          style: TextButton.styleFrom(minimumSize: minSize),
          child: child,
        ),
      AppButtonVariant.destructive => FilledButton(
          onPressed: effectiveOnPressed,
          style: FilledButton.styleFrom(
            minimumSize: minSize,
            backgroundColor: Theme.of(context).colorScheme.error,
            foregroundColor: Theme.of(context).colorScheme.onError,
          ),
          child: child,
        ),
    };
  }
}
