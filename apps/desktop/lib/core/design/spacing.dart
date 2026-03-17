import 'package:flutter/material.dart';

/// Consistent spacing constants for the Praxis desktop app.
class PraxisSpacing {
  PraxisSpacing._();

  static const double xs = 4;
  static const double sm = 8;
  static const double md = 16;
  static const double lg = 24;
  static const double xl = 32;
  static const double xxl = 48;
  static const double xxxl = 64;

  /// Standard page padding.
  static const EdgeInsets pagePadding = EdgeInsets.all(24);

  /// Standard card inner padding.
  static const EdgeInsets cardPadding = EdgeInsets.all(16);

  /// Vertical section separation.
  static const EdgeInsets sectionPadding = EdgeInsets.symmetric(vertical: 24);

  /// Sidebar width when expanded.
  static const double sidebarExpanded = 260;

  /// Sidebar width when collapsed (icon-only).
  static const double sidebarCollapsed = 72;
}
