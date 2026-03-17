import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../app_shell.dart';
import '../../features/auth/login_screen.dart';
import '../../core/design/examples/component_showcase.dart';
import '../../features/dashboard/dashboard_screen.dart';
import '../../features/session/session_list_screen.dart';
import '../../features/session/session_detail_screen.dart';
import '../../features/constraints/constraint_editor_screen.dart';
import '../../features/approval/approval_list_screen.dart';
import '../../features/approval/approval_detail_screen.dart';
import '../../features/delegation/delegation_screen.dart';
import '../../features/settings/settings_screen.dart';

/// GoRouter configuration for the desktop app.
final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authNotifierProvider);

  return GoRouter(
    redirect: (context, state) {
      final isAuthenticated = authState is Authenticated;
      final isLoginRoute = state.matchedLocation == '/login';

      if (!isAuthenticated && !isLoginRoute) return '/login';
      if (isAuthenticated && isLoginRoute) return '/';
      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (_, __) => const LoginScreen(),
      ),
      ShellRoute(
        builder: (_, __, child) => AppShell(child: child),
        routes: [
          GoRoute(
            path: '/',
            builder: (_, __) => const DashboardScreen(),
          ),
          GoRoute(
            path: '/sessions',
            builder: (_, __) => const SessionListScreen(),
          ),
          GoRoute(
            path: '/sessions/:id',
            builder: (_, state) => SessionDetailScreen(
              sessionId: state.pathParameters['id']!,
            ),
          ),
          GoRoute(
            path: '/constraints',
            builder: (_, __) => const ConstraintEditorScreen(),
          ),
          GoRoute(
            path: '/constraints/:sessionId',
            builder: (_, state) => ConstraintEditorScreen(
              sessionId: state.pathParameters['sessionId'],
            ),
          ),
          GoRoute(
            path: '/approvals',
            builder: (_, __) => const ApprovalListScreen(),
          ),
          GoRoute(
            path: '/approvals/:id',
            builder: (_, state) => ApprovalDetailScreen(
              approvalId: state.pathParameters['id']!,
            ),
          ),
          GoRoute(
            path: '/delegations',
            builder: (_, __) => const DelegationScreen(),
          ),
          GoRoute(
            path: '/settings',
            builder: (_, __) => const SettingsScreen(),
          ),
          if (kDebugMode)
            GoRoute(
              path: '/dev/showcase',
              builder: (_, __) => const ComponentShowcase(),
            ),
        ],
      ),
    ],
  );
});
