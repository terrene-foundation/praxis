import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:praxis_shared/praxis_shared.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../auth/desktop_token_storage.dart';

/// Desktop-specific provider overrides.
///
/// These are passed to [ProviderScope] at app startup to inject
/// platform-specific implementations.
List<Override> desktopProviderOverrides({
  String baseUrl = 'http://localhost:8000',
}) {
  return [
    apiConfigProvider.overrideWithValue(
      ApiConfig(baseUrl: baseUrl),
    ),
    tokenStorageProvider.overrideWithValue(
      DesktopTokenStorage(),
    ),
  ];
}

/// Sidebar collapsed state, persisted to SharedPreferences.
final sidebarCollapsedProvider =
    StateNotifierProvider<SidebarCollapsedNotifier, bool>((ref) {
  return SidebarCollapsedNotifier();
});

class SidebarCollapsedNotifier extends StateNotifier<bool> {
  SidebarCollapsedNotifier() : super(false) {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    state = prefs.getBool('sidebar_collapsed') ?? false;
  }

  Future<void> toggle() async {
    state = !state;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('sidebar_collapsed', state);
  }
}

/// Theme mode preference (system, light, dark).
final themeModeProvider =
    StateNotifierProvider<ThemeModeNotifier, ThemeModePreference>((ref) {
  return ThemeModeNotifier();
});

enum ThemeModePreference { system, light, dark }

class ThemeModeNotifier extends StateNotifier<ThemeModePreference> {
  ThemeModeNotifier() : super(ThemeModePreference.system) {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final value = prefs.getString('theme_mode');
    if (value != null) {
      state = ThemeModePreference.values.firstWhere(
        (e) => e.name == value,
        orElse: () => ThemeModePreference.system,
      );
    }
  }

  Future<void> set(ThemeModePreference mode) async {
    state = mode;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('theme_mode', mode.name);
  }
}
