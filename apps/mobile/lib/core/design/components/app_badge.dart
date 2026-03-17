import 'package:flutter/material.dart';

/// Badge variant for mobile status badges.
enum AppBadgeVariant { info, success, warning, error, neutral }

/// A small colored pill displaying a status label.
class AppBadge extends StatelessWidget {
  final String text;
  final AppBadgeVariant variant;

  const AppBadge({
    super.key,
    required this.text,
    this.variant = AppBadgeVariant.neutral,
  });

  @override
  Widget build(BuildContext context) {
    final (bgColor, fgColor) = switch (variant) {
      AppBadgeVariant.info => (Colors.blue.shade50, Colors.blue.shade700),
      AppBadgeVariant.success => (Colors.green.shade50, Colors.green.shade700),
      AppBadgeVariant.warning => (Colors.orange.shade50, Colors.orange.shade700),
      AppBadgeVariant.error => (Colors.red.shade50, Colors.red.shade700),
      AppBadgeVariant.neutral => (Colors.grey.shade100, Colors.grey.shade700),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        text,
        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: fgColor),
      ),
    );
  }
}
