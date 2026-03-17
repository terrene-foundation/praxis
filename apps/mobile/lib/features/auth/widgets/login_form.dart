import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../../core/design/design_system.dart';

/// Login form with email and password fields for mobile.
class LoginForm extends ConsumerStatefulWidget {
  const LoginForm({super.key});

  @override
  ConsumerState<LoginForm> createState() => _LoginFormState();
}

class _LoginFormState extends ConsumerState<LoginForm> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final username = _emailController.text.trim();
    final password = _passwordController.text;
    if (username.isEmpty || password.isEmpty) return;

    await ref
        .read(authNotifierProvider.notifier)
        .login(username, password);
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider);
    final isLoading = authState is AuthLoading;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        AppInput(
          label: 'Username',
          hint: 'your username',
          controller: _emailController,
          keyboardType: TextInputType.text,
          prefixIcon: const Icon(Icons.person_outlined),
          enabled: !isLoading,
        ),
        const SizedBox(height: MobileSpacing.md),
        AppInput(
          label: 'Password',
          controller: _passwordController,
          obscureText: _obscurePassword,
          enabled: !isLoading,
          prefixIcon: const Icon(Icons.lock_outlined),
          suffixIcon: IconButton(
            icon: Icon(
              _obscurePassword
                  ? Icons.visibility_outlined
                  : Icons.visibility_off_outlined,
            ),
            onPressed: () {
              setState(() => _obscurePassword = !_obscurePassword);
            },
          ),
        ),
        const SizedBox(height: MobileSpacing.lg),
        SizedBox(
          width: double.infinity,
          child: AppButton(
            label: 'Log In',
            onPressed: isLoading ? null : _submit,
            isLoading: isLoading,
          ),
        ),
        const SizedBox(height: MobileSpacing.md),
        TextButton(
          onPressed: () {
            // Placeholder for forgot password flow
          },
          child: const Text('Forgot password?'),
        ),
      ],
    );
  }
}
