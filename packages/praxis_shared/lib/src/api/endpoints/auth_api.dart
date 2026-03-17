import 'package:dio/dio.dart';

import '../../models/user.dart';

/// Response from the login endpoint.
///
/// The Praxis backend returns `access_token` and `token_type`.
/// `refresh_token` and `expires_in` are optional — the backend may not
/// issue them.
class AuthTokenResponse {
  final String accessToken;
  final String tokenType;
  final String? refreshToken;
  final int? expiresIn;

  const AuthTokenResponse({
    required this.accessToken,
    required this.tokenType,
    this.refreshToken,
    this.expiresIn,
  });

  factory AuthTokenResponse.fromJson(Map<String, dynamic> json) {
    return AuthTokenResponse(
      accessToken: json['access_token'] as String,
      tokenType: json['token_type'] as String,
      refreshToken: json['refresh_token'] as String?,
      expiresIn: json['expires_in'] as int?,
    );
  }
}

/// API endpoints for authentication.
class AuthApi {
  final Dio _dio;

  AuthApi(this._dio);

  /// Login with username and password.
  Future<AuthTokenResponse> login(String username, String password) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/auth/login',
      data: {'username': username, 'password': password},
    );
    return AuthTokenResponse.fromJson(response.data!);
  }

  /// Refresh the access token using a refresh token.
  Future<AuthTokenResponse> refresh(String refreshToken) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/auth/refresh',
      data: {'refresh_token': refreshToken},
    );
    return AuthTokenResponse.fromJson(response.data!);
  }

  /// Logout (invalidate tokens server-side).
  Future<void> logout(String refreshToken) async {
    await _dio.post<void>(
      '/auth/logout',
      data: {'refresh_token': refreshToken},
    );
  }

  /// Get the current authenticated user's profile.
  Future<User> me() async {
    final response =
        await _dio.get<Map<String, dynamic>>('/auth/me');
    return User.fromJson(response.data!);
  }
}
