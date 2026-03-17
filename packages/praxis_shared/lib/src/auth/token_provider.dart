import 'auth_state.dart';

/// Provides the current access token to the API interceptor.
///
/// Wraps the auth state and extracts the token only when authenticated.
class TokenProvider {
  final AuthState _authState;

  TokenProvider(this._authState);

  /// The current JWT access token, or null if not authenticated.
  String? get accessToken {
    return _authState.maybeMap(
      authenticated: (state) => state.accessToken,
      orElse: () => null,
    );
  }
}
