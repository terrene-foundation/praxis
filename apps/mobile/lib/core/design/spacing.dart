import 'package:flutter/material.dart';

/// Touch-optimized spacing constants for the Praxis mobile app.
class MobileSpacing {
  MobileSpacing._();

  static const double xs = 4;
  static const double sm = 8;
  static const double md = 16;
  static const double lg = 24;
  static const double xl = 32;

  /// Page padding (tighter than desktop for screen real estate).
  static const EdgeInsets pagePadding =
      EdgeInsets.symmetric(horizontal: 16, vertical: 8);

  /// Card inner padding.
  static const EdgeInsets cardPadding = EdgeInsets.all(16);

  /// List item padding.
  static const EdgeInsets listItemPadding =
      EdgeInsets.symmetric(horizontal: 16, vertical: 12);

  /// Minimum touch target size per Material guideline.
  static const double minTouchTarget = 48;
}
