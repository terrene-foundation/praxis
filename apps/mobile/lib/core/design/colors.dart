// Re-export the shared color palette from the desktop design system.
// Both platforms use identical semantic colors for visual consistency.
// Import directly from praxis_shared or define mobile-specific overrides here.

import 'package:flutter/material.dart';

/// Praxis color palette -- shared across desktop and mobile.
class PraxisColors {
  PraxisColors._();

  static const primary = Color(0xFF3F51B5);
  static const onPrimary = Color(0xFFFFFFFF);
  static const primaryContainer = Color(0xFFDDE1FF);
  static const onPrimaryContainer = Color(0xFF001452);

  static const secondary = Color(0xFF009688);
  static const onSecondary = Color(0xFFFFFFFF);
  static const secondaryContainer = Color(0xFFB2DFDB);
  static const onSecondaryContainer = Color(0xFF00201C);

  // Trust state colors
  static const trustHealthy = Color(0xFF4CAF50);
  static const trustCaution = Color(0xFFFFC107);
  static const trustWarning = Color(0xFFFF9800);
  static const trustViolation = Color(0xFFF44336);
  static const trustHeld = Color(0xFF9C27B0);

  // Session status
  static const sessionActive = Color(0xFF4CAF50);
  static const sessionPaused = Color(0xFFFFC107);
  static const sessionEnded = Color(0xFF9E9E9E);

  // Constraint dimensions
  static const constraintFinancial = Color(0xFF2196F3);
  static const constraintOperational = Color(0xFF4CAF50);
  static const constraintTemporal = Color(0xFFFF9800);
  static const constraintDataAccess = Color(0xFF9C27B0);
  static const constraintCommunication = Color(0xFF00BCD4);
}
