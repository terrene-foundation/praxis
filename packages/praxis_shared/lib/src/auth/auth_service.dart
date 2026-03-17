import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:logger/logger.dart';

import '../api/endpoints/auth_api.dart';
import '../models/user.dart';
import 'auth_state.dart';
import 'token_storage.dart';

/// Core authentication service (platform-independent).
///
/// Handles login, token refresh, session restoration, and logout.
/// Platform-specific features (biometrics, system tray) are layered
/// on top by each app.
class AuthService {
  final AuthApi _authApi;
  final TokenStorage _tokenStorage;
  final Logger _logger = Logger();
  Timer? _refreshTimer;

  AuthService({
    required AuthApi authApi,
    required TokenStorage tokenStorage,
  })  : _authApi = authApi,
        _tokenStorage = tokenStorage;

  /// Login with username and password.
  Future<AuthState> login(String username, String password) async {
    try {
      final response = await _authApi.login(username, password);
      final refreshToken = response.refreshToken ?? '';
      await _tokenStorage.saveTokens(
        access: response.accessToken,
        refresh: refreshToken,
      );

      final user = _decodeUserFromToken(response.accessToken);
      final expiresAt = _tokenExpiry(response.accessToken);

      _scheduleRefresh(expiresAt);

      return AuthState.authenticated(
        currentUser: user,
        accessToken: response.accessToken,
        refreshToken: refreshToken,
        expiresAt: expiresAt,
      );
    } on DioException catch (e) {
      _logger.e('Login failed', error: e);
      final message = e.response?.statusCode == 401
          ? 'Invalid username or password.'
          : 'Unable to connect. Please check your network.';
      return AuthState.unauthenticated(message: message);
    } catch (e) {
      _logger.e('Login failed', error: e);
      return const AuthState.error(
        message: 'An unexpected error occurred during login.',
      );
    }
  }

  /// Refresh the access token using the stored refresh token.
  Future<AuthState> refreshToken() async {
    try {
      final storedRefresh = await _tokenStorage.getRefreshToken();
      if (storedRefresh == null) {
        return const AuthState.unauthenticated(
          message: 'Session expired. Please log in again.',
        );
      }

      final response = await _authApi.refresh(storedRefresh);
      final refreshToken = response.refreshToken ?? storedRefresh;
      await _tokenStorage.saveTokens(
        access: response.accessToken,
        refresh: refreshToken,
      );

      final user = _decodeUserFromToken(response.accessToken);
      final expiresAt = _tokenExpiry(response.accessToken);

      _scheduleRefresh(expiresAt);

      return AuthState.authenticated(
        currentUser: user,
        accessToken: response.accessToken,
        refreshToken: refreshToken,
        expiresAt: expiresAt,
      );
    } catch (e) {
      _logger.e('Token refresh failed', error: e);
      await _tokenStorage.clearTokens();
      return const AuthState.unauthenticated(
        message: 'Session expired. Please log in again.',
      );
    }
  }

  /// Restore a session from stored tokens on app startup.
  Future<AuthState> restoreSession() async {
    try {
      final accessToken = await _tokenStorage.getAccessToken();
      if (accessToken == null) {
        return const AuthState.unauthenticated();
      }

      if (_isTokenExpired(accessToken)) {
        return await refreshToken();
      }

      final user = _decodeUserFromToken(accessToken);
      final expiresAt = _tokenExpiry(accessToken);
      final refreshTokenValue = await _tokenStorage.getRefreshToken();

      if (refreshTokenValue == null) {
        return const AuthState.unauthenticated();
      }

      _scheduleRefresh(expiresAt);

      return AuthState.authenticated(
        currentUser: user,
        accessToken: accessToken,
        refreshToken: refreshTokenValue,
        expiresAt: expiresAt,
      );
    } catch (e) {
      _logger.e('Session restore failed', error: e);
      return const AuthState.unauthenticated();
    }
  }

  /// Logout and clear all stored credentials.
  Future<void> logout() async {
    _refreshTimer?.cancel();
    try {
      final refreshTokenValue = await _tokenStorage.getRefreshToken();
      if (refreshTokenValue != null) {
        await _authApi.logout(refreshTokenValue);
      }
    } catch (e) {
      _logger.w('Server logout failed (token may already be invalid)', error: e);
    } finally {
      await _tokenStorage.clearTokens();
    }
  }

  /// Schedule a token refresh 60 seconds before the access token expires.
  void _scheduleRefresh(DateTime expiresAt) {
    _refreshTimer?.cancel();
    final refreshAt = expiresAt.subtract(const Duration(seconds: 60));
    final delay = refreshAt.difference(DateTime.now());
    if (delay.isNegative) {
      refreshToken();
    } else {
      _refreshTimer = Timer(delay, () => refreshToken());
    }
  }

  /// Decode the user payload from a JWT access token.
  User _decodeUserFromToken(String jwt) {
    final parts = jwt.split('.');
    if (parts.length != 3) {
      throw const FormatException('Invalid JWT format');
    }
    final payload = _decodeBase64(parts[1]);
    final data = jsonDecode(payload) as Map<String, dynamic>;
    return User(
      id: data['sub'] as String? ?? '',
      email: data['email'] as String? ?? '',
      displayName: data['name'] as String? ?? '',
      role: UserRole.values.firstWhere(
        (r) => r.name == data['role'],
        orElse: () => UserRole.collaborator,
      ),
      avatarUrl: data['avatar_url'] as String?,
    );
  }

  /// Extract the expiry time from a JWT.
  DateTime _tokenExpiry(String jwt) {
    final parts = jwt.split('.');
    if (parts.length != 3) return DateTime.now();
    final payload = _decodeBase64(parts[1]);
    final data = jsonDecode(payload) as Map<String, dynamic>;
    final exp = data['exp'] as int?;
    if (exp == null) return DateTime.now().add(const Duration(hours: 1));
    return DateTime.fromMillisecondsSinceEpoch(exp * 1000);
  }

  /// Check whether a JWT has expired.
  bool _isTokenExpired(String jwt) {
    final expiry = _tokenExpiry(jwt);
    return DateTime.now().isAfter(expiry);
  }

  /// Decode base64url-encoded JWT payload segment.
  String _decodeBase64(String input) {
    var normalized = input.replaceAll('-', '+').replaceAll('_', '/');
    switch (normalized.length % 4) {
      case 0:
        break;
      case 2:
        normalized += '==';
        break;
      case 3:
        normalized += '=';
        break;
      default:
        throw const FormatException('Invalid base64 string');
    }
    return utf8.decode(base64.decode(normalized));
  }

  /// Cancel any pending refresh timer (for disposal).
  void dispose() {
    _refreshTimer?.cancel();
  }
}
