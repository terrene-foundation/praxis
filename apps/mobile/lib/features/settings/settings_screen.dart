import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:praxis_shared/praxis_shared.dart';

import '../../core/design/design_system.dart';
import '../../core/providers/app_providers.dart';

/// Settings screen for the mobile app.
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final themeMode = ref.watch(themeModeProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          Padding(
            padding: const EdgeInsets.all(MobileSpacing.md),
            child: Text(
              'Appearance',
              style: theme.textTheme.titleMedium,
            ),
          ),
          RadioGroup<ThemeModePreference>(
            groupValue: themeMode,
            onChanged: (v) {
              if (v != null) {
                ref.read(themeModeProvider.notifier).set(v);
              }
            },
            child: const Column(
              children: [
                RadioListTile<ThemeModePreference>(
                  title: Text('System'),
                  value: ThemeModePreference.system,
                ),
                RadioListTile<ThemeModePreference>(
                  title: Text('Light'),
                  value: ThemeModePreference.light,
                ),
                RadioListTile<ThemeModePreference>(
                  title: Text('Dark'),
                  value: ThemeModePreference.dark,
                ),
              ],
            ),
          ),
          const Divider(),
          Padding(
            padding: const EdgeInsets.all(MobileSpacing.md),
            child: Text(
              'Account',
              style: theme.textTheme.titleMedium,
            ),
          ),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Log out'),
            onTap: () {
              ref.read(authNotifierProvider.notifier).logout();
            },
          ),
          if (kDebugMode) ...[
            const Divider(),
            Padding(
              padding: const EdgeInsets.all(MobileSpacing.md),
              child: Text(
                'Developer',
                style: theme.textTheme.titleMedium,
              ),
            ),
            ListTile(
              leading: const Icon(Icons.palette_outlined),
              title: const Text('Component Showcase'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.go('/settings/showcase'),
            ),
          ],
        ],
      ),
    );
  }
}
