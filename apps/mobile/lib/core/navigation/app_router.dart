import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../app_shell.dart';
import '../../features/auth/login_screen.dart';
import '../../features/session/session_list_screen.dart';
import '../../features/session/session_detail_screen.dart';
import '../../features/approval/approval_list_screen.dart';
import '../../features/approval/approval_detail_screen.dart';
import '../../features/trust/trust_chain_list_screen.dart';
import '../../features/trust/trust_entry_detail_screen.dart';
import '../../features/settings/settings_screen.dart';
import '../../core/design/examples/component_showcase.dart';

/// GoRouter configuration for the mobile app.
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
      StatefulShellRoute.indexedStack(
        builder: (_, __, navigationShell) =>
            AppShell(navigationShell: navigationShell),
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/',
                builder: (_, __) => const SessionListScreen(),
              ),
              GoRoute(
                path: '/sessions/:id',
                builder: (_, state) => SessionDetailScreen(
                  sessionId: state.pathParameters['id']!,
                ),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
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
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/trust',
                builder: (_, __) => const TrustChainListScreen(),
              ),
              GoRoute(
                path: '/trust/:id',
                builder: (_, state) => TrustEntryDetailScreen(
                  entryId: state.pathParameters['id']!,
                ),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/settings',
                builder: (_, __) => const SettingsScreen(),
              ),
              if (kDebugMode)
                GoRoute(
                  path: '/settings/showcase',
                  builder: (_, __) => const ComponentShowcase(),
                ),
            ],
          ),
        ],
      ),
    ],
  );
});
