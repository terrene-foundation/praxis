import 'package:flutter/material.dart';

/// Navigation destinations for the desktop sidebar.
enum NavDestination {
  dashboard(
    icon: Icons.dashboard_outlined,
    activeIcon: Icons.dashboard,
    label: 'Dashboard',
    path: '/',
  ),
  sessions(
    icon: Icons.layers_outlined,
    activeIcon: Icons.layers,
    label: 'Sessions',
    path: '/sessions',
  ),
  constraints(
    icon: Icons.tune_outlined,
    activeIcon: Icons.tune,
    label: 'Constraints',
    path: '/constraints',
  ),
  approvals(
    icon: Icons.approval_outlined,
    activeIcon: Icons.approval,
    label: 'Approvals',
    path: '/approvals',
  ),
  delegations(
    icon: Icons.people_outline,
    activeIcon: Icons.people,
    label: 'Delegations',
    path: '/delegations',
  ),
  settings(
    icon: Icons.settings_outlined,
    activeIcon: Icons.settings,
    label: 'Settings',
    path: '/settings',
  );

  final IconData icon;
  final IconData activeIcon;
  final String label;
  final String path;

  const NavDestination({
    required this.icon,
    required this.activeIcon,
    required this.label,
    required this.path,
  });
}
