import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/design/design_system.dart';
import '../../core/providers/app_providers.dart';

/// Settings screen for the desktop app.
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final themeMode = ref.watch(themeModeProvider);

    return Scaffold(
      body: Padding(
        padding: PraxisSpacing.pagePadding,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Settings', style: theme.textTheme.headlineMedium),
            const SizedBox(height: PraxisSpacing.lg),
            AppCard(
              title: 'Appearance',
              child: RadioGroup<ThemeModePreference>(
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
            ),
            if (kDebugMode) ...[
              const SizedBox(height: PraxisSpacing.md),
              AppCard(
                title: 'Developer',
                child: ListTile(
                  leading: const Icon(Icons.palette_outlined),
                  title: const Text('Component Showcase'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.go('/dev/showcase'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
