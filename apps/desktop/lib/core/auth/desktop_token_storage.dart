import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:praxis_shared/praxis_shared.dart';

/// Desktop-specific token storage using flutter_secure_storage.
///
/// Platform backends:
/// - macOS: Keychain
/// - Windows: Windows Credential Manager
/// - Linux: libsecret
class DesktopTokenStorage implements TokenStorage {
  final FlutterSecureStorage _storage;

  DesktopTokenStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const _accessTokenKey = 'praxis_access_token';
  static const _refreshTokenKey = 'praxis_refresh_token';

  @override
  Future<void> saveTokens({
    required String access,
    required String refresh,
  }) async {
    await _storage.write(key: _accessTokenKey, value: access);
    await _storage.write(key: _refreshTokenKey, value: refresh);
  }

  @override
  Future<String?> getAccessToken() =>
      _storage.read(key: _accessTokenKey);

  @override
  Future<String?> getRefreshToken() =>
      _storage.read(key: _refreshTokenKey);

  @override
  Future<void> clearTokens() async {
    await _storage.delete(key: _accessTokenKey);
    await _storage.delete(key: _refreshTokenKey);
  }
}
