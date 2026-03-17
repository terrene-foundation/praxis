import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';
import 'widgets/login_form.dart';

/// Mobile login screen -- full-screen, keyboard-aware, no app bar.
class LoginScreen extends ConsumerWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authNotifierProvider);
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: MobileSpacing.pagePadding,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.shield_outlined,
                  size: 56,
                  color: theme.colorScheme.primary,
                ),
                const SizedBox(height: MobileSpacing.md),
                Text(
                  'Welcome to Praxis',
                  style: theme.textTheme.headlineMedium,
                ),
                const SizedBox(height: MobileSpacing.xs),
                Text(
                  'Trust-aware collaboration',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.outline,
                  ),
                ),
                const SizedBox(height: MobileSpacing.xl),
                const LoginForm(),
                if (authState is Unauthenticated &&
                    authState.message != null) ...[
                  const SizedBox(height: MobileSpacing.md),
                  Text(
                    authState.message!,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.error,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
                if (authState is AuthError) ...[
                  const SizedBox(height: MobileSpacing.md),
                  Text(
                    authState.message,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.error,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
                const SizedBox(height: MobileSpacing.xl),
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
    );
  }
}
