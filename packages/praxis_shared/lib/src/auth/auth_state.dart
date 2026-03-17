import 'package:freezed_annotation/freezed_annotation.dart';

import '../models/user.dart';

part 'auth_state.freezed.dart';

/// Authentication state for the Praxis application.
///
/// The app reacts to state changes: unauthenticated users see the login
/// screen, authenticated users see the main application shell.
@freezed
class AuthState with _$AuthState {
  /// Initial state before session restoration attempt.
  const factory AuthState.initial() = AuthInitial;

  /// Authentication is in progress (login, refresh, or restore).
  const factory AuthState.loading() = AuthLoading;

  /// Successfully authenticated with valid tokens.
  const factory AuthState.authenticated({
    required User currentUser,
    required String accessToken,
    required String refreshToken,
    required DateTime expiresAt,
  }) = Authenticated;

  /// Not authenticated. Optional message explains why (e.g. session expired).
  const factory AuthState.unauthenticated({String? message}) = Unauthenticated;

  /// Authentication failed with an error.
  const factory AuthState.error({required String message}) = AuthError;
}
