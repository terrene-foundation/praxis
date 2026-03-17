import 'package:flutter/material.dart';

/// Elevation shadow presets for the Praxis desktop app.
class PraxisShadows {
  PraxisShadows._();

  /// No shadow -- flat card style.
  static const List<BoxShadow> flat = [];

  /// Subtle shadow for raised cards.
  static const List<BoxShadow> raised = [
    BoxShadow(
      color: Color(0x1A000000),
      blurRadius: 4,
      offset: Offset(0, 2),
    ),
  ];

  /// Prominent shadow for floating elements (dialogs, popovers).
  static const List<BoxShadow> floating = [
    BoxShadow(
      color: Color(0x33000000),
      blurRadius: 16,
      offset: Offset(0, 8),
    ),
  ];
}
