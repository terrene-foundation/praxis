import 'package:flutter/material.dart';

/// Praxis color palette for light mode.
///
/// Based on Material 3 color system with trust-state and constraint-dimension
/// semantic colors specific to the CO methodology.
class PraxisColors {
  PraxisColors._();

  // Primary: deep indigo -- conveys trust, stability
  static const primary = Color(0xFF3F51B5);
  static const onPrimary = Color(0xFFFFFFFF);
  static const primaryContainer = Color(0xFFDDE1FF);
  static const onPrimaryContainer = Color(0xFF001452);

  // Secondary: teal -- conveys collaboration, growth
  static const secondary = Color(0xFF009688);
  static const onSecondary = Color(0xFFFFFFFF);
  static const secondaryContainer = Color(0xFFB2DFDB);
  static const onSecondaryContainer = Color(0xFF00201C);

  // Surface
  static const surface = Color(0xFFFAFAFA);
  static const onSurface = Color(0xFF1C1B1F);
  static const surfaceContainerHighest = Color(0xFFE6E0E9);

  // Error
  static const error = Color(0xFFB3261E);
  static const onError = Color(0xFFFFFFFF);

  // -- Trust state colors --
  static const trustHealthy = Color(0xFF4CAF50);
  static const trustCaution = Color(0xFFFFC107);
  static const trustWarning = Color(0xFFFF9800);
  static const trustViolation = Color(0xFFF44336);
  static const trustHeld = Color(0xFF9C27B0);

  // -- Session status colors --
  static const sessionActive = Color(0xFF4CAF50);
  static const sessionPaused = Color(0xFFFFC107);
  static const sessionEnded = Color(0xFF9E9E9E);

  // -- Constraint dimension colors --
  static const constraintFinancial = Color(0xFF2196F3);
  static const constraintOperational = Color(0xFF4CAF50);
  static const constraintTemporal = Color(0xFFFF9800);
  static const constraintDataAccess = Color(0xFF9C27B0);
  static const constraintCommunication = Color(0xFF00BCD4);
}

/// Praxis color palette for dark mode.
class PraxisColorsDark {
  PraxisColorsDark._();

  static const primary = Color(0xFFBBC3FF);
  static const onPrimary = Color(0xFF08218A);
  static const primaryContainer = Color(0xFF293CA0);
  static const onPrimaryContainer = Color(0xFFDDE1FF);

  static const secondary = Color(0xFF80CBC4);
  static const onSecondary = Color(0xFF003731);
  static const secondaryContainer = Color(0xFF005048);
  static const onSecondaryContainer = Color(0xFFB2DFDB);

  static const surface = Color(0xFF1C1B1F);
  static const onSurface = Color(0xFFE6E1E5);
  static const surfaceContainerHighest = Color(0xFF49454F);

  static const error = Color(0xFFF2B8B5);
  static const onError = Color(0xFF601410);

  // Trust state colors remain consistent across themes
  static const trustHealthy = Color(0xFF66BB6A);
  static const trustCaution = Color(0xFFFFCA28);
  static const trustWarning = Color(0xFFFFA726);
  static const trustViolation = Color(0xFFEF5350);
  static const trustHeld = Color(0xFFAB47BC);

  static const sessionActive = Color(0xFF66BB6A);
  static const sessionPaused = Color(0xFFFFCA28);
  static const sessionEnded = Color(0xFFBDBDBD);

  static const constraintFinancial = Color(0xFF42A5F5);
  static const constraintOperational = Color(0xFF66BB6A);
  static const constraintTemporal = Color(0xFFFFA726);
  static const constraintDataAccess = Color(0xFFAB47BC);
  static const constraintCommunication = Color(0xFF26C6DA);
}
