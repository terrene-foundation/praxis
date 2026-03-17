import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/design/theme.dart';
import 'core/navigation/app_router.dart';
import 'core/providers/app_providers.dart';

/// Root widget for the Praxis desktop application.
class PraxisDesktopApp extends ConsumerWidget {
  const PraxisDesktopApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    final themeMode = ref.watch(themeModeProvider);

    return MaterialApp.router(
      title: 'Praxis',
      debugShowCheckedModeBanner: false,
      theme: praxisLightTheme(),
      darkTheme: praxisDarkTheme(),
      themeMode: switch (themeMode) {
        ThemeModePreference.system => ThemeMode.system,
        ThemeModePreference.light => ThemeMode.light,
        ThemeModePreference.dark => ThemeMode.dark,
      },
      routerConfig: router,
    );
  }
}
