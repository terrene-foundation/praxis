import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:praxis_shared/praxis_shared.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../auth/biometric_service.dart';
import '../auth/mobile_token_storage.dart';

/// Mobile-specific provider overrides.
List<Override> mobileProviderOverrides({
  String baseUrl = 'http://localhost:8000',
}) {
  return [
    apiConfigProvider.overrideWithValue(
      ApiConfig(baseUrl: baseUrl),
    ),
    tokenStorageProvider.overrideWithValue(
      MobileTokenStorage(),
    ),
  ];
}

/// Biometric authentication service.
final biometricServiceProvider = Provider<BiometricService>((ref) {
  return BiometricService();
});

/// Whether biometric authentication is available on this device.
final biometricAvailableProvider = FutureProvider<bool>((ref) async {
  return ref.watch(biometricServiceProvider).isAvailable();
});

/// Mobile token storage (exposes biometric preferences).
final mobileTokenStorageProvider = Provider<MobileTokenStorage>((ref) {
  return MobileTokenStorage();
});

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
