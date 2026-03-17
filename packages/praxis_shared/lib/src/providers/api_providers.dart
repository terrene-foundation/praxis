import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/endpoints/auth_api.dart';
import '../api/praxis_client.dart';
import '../auth/auth_service.dart';
import '../auth/auth_state.dart';
import '../auth/token_provider.dart';
import '../auth/token_storage.dart';
import '../models/api_config.dart';
import '../models/delegation.dart';
import '../models/deliberation_record.dart';
import '../models/held_action.dart';
import '../models/session.dart';
import '../models/user.dart';
import '../services/websocket_service.dart';

// ---------------------------------------------------------------------------
// Configuration providers -- overridden by each platform app
// ---------------------------------------------------------------------------

/// API configuration (base URL, timeouts). Override per platform.
final apiConfigProvider = Provider<ApiConfig>((ref) {
  return const ApiConfig(baseUrl: 'http://localhost:8000');
});

/// Token storage implementation. Override per platform with secure storage.
final tokenStorageProvider = Provider<TokenStorage>((ref) {
  throw UnimplementedError(
    'tokenStorageProvider must be overridden with a platform-specific '
    'TokenStorage implementation.',
  );
});

// ---------------------------------------------------------------------------
// Auth providers
// ---------------------------------------------------------------------------

/// Auth API endpoint (uses its own Dio without auth interceptor to avoid
/// circular dependency).
final authApiProvider = Provider<AuthApi>((ref) {
  final config = ref.watch(apiConfigProvider);
  final client = PraxisClient(
    baseUrl: config.baseUrl,
    tokenProvider: TokenProvider(const AuthState.unauthenticated()),
    connectTimeout: config.connectTimeout,
    receiveTimeout: config.receiveTimeout,
  );
  return client.auth;
});

/// Core authentication service.
final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService(
    authApi: ref.watch(authApiProvider),
    tokenStorage: ref.watch(tokenStorageProvider),
  );
});

/// Current authentication state as a state notifier.
final authNotifierProvider =
    StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.watch(authServiceProvider));
});

/// Auth state notifier -- manages login, logout, restore, and refresh.
class AuthNotifier extends StateNotifier<AuthState> {
  final AuthService _service;

  AuthNotifier(this._service) : super(const AuthState.initial());

  Future<void> login(String username, String password) async {
    state = const AuthState.loading();
    state = await _service.login(username, password);
  }

  Future<void> restoreSession() async {
    state = const AuthState.loading();
    state = await _service.restoreSession();
  }

  Future<void> refreshToken() async {
    state = await _service.refreshToken();
  }

  Future<void> logout() async {
    await _service.logout();
    state = const AuthState.unauthenticated();
  }
}

/// Current user (null if not authenticated).
final currentUserProvider = Provider<User?>((ref) {
  final authState = ref.watch(authNotifierProvider);
  return authState.maybeMap(
    authenticated: (state) => state.currentUser,
    orElse: () => null,
  );
});

/// Whether the user is currently authenticated.
final isAuthenticatedProvider = Provider<bool>((ref) {
  return ref.watch(authNotifierProvider) is Authenticated;
});

/// Token provider for the API client interceptor.
final tokenProviderProvider = Provider<TokenProvider>((ref) {
  return TokenProvider(ref.watch(authNotifierProvider));
});

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------

/// The main Praxis API client, authenticated and ready to use.
final praxisClientProvider = Provider<PraxisClient>((ref) {
  final config = ref.watch(apiConfigProvider);
  final tokenProvider = ref.watch(tokenProviderProvider);
  return PraxisClient(
    baseUrl: config.baseUrl,
    tokenProvider: tokenProvider,
    connectTimeout: config.connectTimeout,
    receiveTimeout: config.receiveTimeout,
  );
});

// ---------------------------------------------------------------------------
// Data providers
// ---------------------------------------------------------------------------

/// All active sessions.
final activeSessionsProvider = FutureProvider<List<Session>>((ref) async {
  final client = ref.watch(praxisClientProvider);
  return client.sessions.listActive();
});

/// A single session by ID.
final sessionProvider =
    FutureProvider.family<Session, String>((ref, id) async {
  final client = ref.watch(praxisClientProvider);
  return client.sessions.get(id);
});

/// Pending held actions awaiting approval.
final pendingApprovalsProvider =
    FutureProvider<List<HeldAction>>((ref) async {
  final client = ref.watch(praxisClientProvider);
  return client.approvals.listPending();
});

/// Number of pending approvals (for badge display).
final pendingApprovalCountProvider = Provider<int>((ref) {
  final approvals = ref.watch(pendingApprovalsProvider);
  return approvals.maybeWhen(data: (list) => list.length, orElse: () => 0);
});

/// Deliberation timeline for a session.
final sessionTimelineProvider =
    FutureProvider.family<List<DeliberationRecord>, String>((ref, sessionId) async {
  final client = ref.watch(praxisClientProvider);
  return client.sessions.timeline(sessionId);
});

/// All delegations.
final delegationsProvider = FutureProvider<List<Delegation>>((ref) async {
  final client = ref.watch(praxisClientProvider);
  return client.delegations.list();
});

// ---------------------------------------------------------------------------
// WebSocket
// ---------------------------------------------------------------------------

/// Derives the WebSocket URL from the API base URL.
///
/// `http://host:port` becomes `ws://host:port/ws/events`.
/// `https://host:port` becomes `wss://host:port/ws/events`.
final wsUrlProvider = Provider<String>((ref) {
  final config = ref.watch(apiConfigProvider);
  final httpUrl = config.baseUrl;
  final wsScheme = httpUrl.startsWith('https') ? 'wss' : 'ws';
  final authority = httpUrl.replaceFirst(RegExp(r'^https?://'), '');
  return '$wsScheme://$authority/ws/events';
});

/// WebSocket service singleton.
final webSocketServiceProvider = Provider<WebSocketService>((ref) {
  final service = WebSocketService();
  ref.onDispose(() => service.dispose());
  return service;
});

/// WebSocket connection state stream.
final wsConnectionStateProvider = StreamProvider<ConnectionState>((ref) {
  final ws = ref.watch(webSocketServiceProvider);
  return ws.stateChanges;
});
