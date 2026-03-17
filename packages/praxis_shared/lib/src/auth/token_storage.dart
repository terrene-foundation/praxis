/// Platform-independent interface for secure token storage.
///
/// Each platform (desktop, mobile) provides its own implementation using
/// the appropriate secure storage mechanism (Keychain, Credential Manager,
/// libsecret, etc.).
abstract class TokenStorage {
  /// Persist both access and refresh tokens.
  Future<void> saveTokens({
    required String access,
    required String refresh,
  });

  /// Retrieve the stored access token, or null if none exists.
  Future<String?> getAccessToken();

  /// Retrieve the stored refresh token, or null if none exists.
  Future<String?> getRefreshToken();

  /// Clear all stored tokens (used on logout).
  Future<void> clearTokens();
}
