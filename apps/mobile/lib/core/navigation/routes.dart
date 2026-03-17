import 'package:flutter/material.dart';

/// Navigation tab destinations for the mobile app.
enum MobileNavTab {
  sessions(
    icon: Icons.layers_outlined,
    activeIcon: Icons.layers,
    label: 'Sessions',
  ),
  approvals(
    icon: Icons.approval_outlined,
    activeIcon: Icons.approval,
    label: 'Approvals',
  ),
  trust(
    icon: Icons.shield_outlined,
    activeIcon: Icons.shield,
    label: 'Trust',
  ),
  settings(
    icon: Icons.settings_outlined,
    activeIcon: Icons.settings,
    label: 'Settings',
  );

  final IconData icon;
  final IconData activeIcon;
  final String label;

  const MobileNavTab({
    required this.icon,
    required this.activeIcon,
    required this.label,
  });
}
