import 'package:local_auth/local_auth.dart';

/// Service for biometric authentication (Face ID, Touch ID, fingerprint).
class BiometricService {
  final LocalAuthentication _localAuth = LocalAuthentication();

  /// Check if biometric authentication is available on this device.
  Future<bool> isAvailable() async {
    final canCheck = await _localAuth.canCheckBiometrics;
    final isDeviceSupported = await _localAuth.isDeviceSupported();
    return canCheck && isDeviceSupported;
  }

  /// Get available biometric types on this device.
  Future<List<BiometricType>> getAvailableTypes() async {
    return _localAuth.getAvailableBiometrics();
  }

  /// Authenticate using biometrics. Returns true on success.
  Future<bool> authenticate({
    String reason = 'Authenticate to access Praxis',
  }) async {
    return _localAuth.authenticate(
      localizedReason: reason,
      options: const AuthenticationOptions(
        stickyAuth: true,
        biometricOnly: false, // Allow PIN/pattern as fallback
      ),
    );
  }

  /// Human-readable name for the biometric type available.
  String getBiometricTypeName(List<BiometricType> types) {
    if (types.contains(BiometricType.face)) return 'Face ID';
    if (types.contains(BiometricType.fingerprint)) return 'Fingerprint';
    if (types.contains(BiometricType.iris)) return 'Iris';
    return 'Biometric';
  }
}
