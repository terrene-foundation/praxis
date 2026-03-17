import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';
import 'widgets/login_form.dart';

/// Full-screen login screen for the desktop app.
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  bool _autoLoginAttempted = false;

  @override
  void initState() {
    super.initState();
    // In debug mode, attempt auto-login so Marionette and dev testing
    // can bypass the login screen without manual text entry.
    if (kDebugMode && !_autoLoginAttempted) {
      _autoLoginAttempted = true;
      Future.microtask(() {
        ref.read(authNotifierProvider.notifier).login('dev', 'dev');
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider);
    final theme = Theme.of(context);

    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          child: SizedBox(
            width: 400,
            child: AppCard(
              elevation: AppCardElevation.raised,
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.shield_outlined,
                    size: 48,
                    color: theme.colorScheme.primary,
                  ),
                  const SizedBox(height: PraxisSpacing.md),
                  Text(
                    'Praxis',
                    style: theme.textTheme.headlineMedium,
                  ),
                  const SizedBox(height: PraxisSpacing.xs),
                  Text(
                    'Trust-aware collaboration',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.outline,
                    ),
                  ),
                  const SizedBox(height: PraxisSpacing.xl),
                  const LoginForm(),
                  if (authState is Unauthenticated &&
                      authState.message != null) ...[
                    const SizedBox(height: PraxisSpacing.md),
                    Text(
                      authState.message!,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.error,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                  if (authState is AuthError) ...[
                    const SizedBox(height: PraxisSpacing.md),
                    Text(
                      authState.message,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.error,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                  const SizedBox(height: PraxisSpacing.xl),
                  Text(
                    'Terrene Foundation',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: theme.colorScheme.outline,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
