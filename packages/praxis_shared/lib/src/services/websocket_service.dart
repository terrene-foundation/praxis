import 'dart:async';
import 'dart:convert';

import 'package:logger/logger.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import 'reconnection_strategy.dart';
import 'websocket_events.dart';

/// Connection state for the WebSocket service.
enum ConnectionState {
  disconnected,
  connecting,
  connected,
  reconnecting,
}

/// Maps snake_case event types from the backend to the camelCase
/// `runtimeType` values expected by the Freezed-generated [WebSocketEvent]
/// deserializer.
const _backendEventTypeMap = <String, String>{
  'session_state_changed': 'sessionUpdated',
  'session_created': 'sessionCreated',
  'session_ended': 'sessionEnded',
  'constraint_updated': 'constraintUpdated',
  'constraint_violation': 'constraintViolation',
  'held_action_created': 'actionHeld',
  'held_action_resolved': 'actionResolved',
  'deliberation_recorded': 'trustEntryAdded',
  'heartbeat': 'heartbeat',
  'error': 'error',
};

/// Real-time event streaming service over WebSocket.
///
/// Connects to the Praxis backend WebSocket endpoint at `/ws/events`,
/// parses incoming events into typed [WebSocketEvent] objects, and provides
/// a stream for consumers.  Includes automatic reconnection with exponential
/// backoff and heartbeat monitoring.
class WebSocketService {
  WebSocketChannel? _channel;
  final ReconnectionStrategy _reconnection = ReconnectionStrategy();
  final StreamController<WebSocketEvent> _eventController =
      StreamController<WebSocketEvent>.broadcast();
  final StreamController<ConnectionState> _stateController =
      StreamController<ConnectionState>.broadcast();
  Timer? _heartbeatTimer;
  ConnectionState _state = ConnectionState.disconnected;
  String? _url;
  String? _token;
  final Logger _logger = Logger();

  static const _heartbeatTimeout = Duration(seconds: 45);

  /// Stream of parsed WebSocket events.
  Stream<WebSocketEvent> get events => _eventController.stream;

  /// Stream of connection state changes.
  Stream<ConnectionState> get stateChanges => _stateController.stream;

  /// Current connection state.
  ConnectionState get state => _state;

  /// Connect to the Praxis WebSocket endpoint.
  Future<void> connect(String url, String token) async {
    _url = url;
    _token = token;
    await _doConnect();
  }

  Future<void> _doConnect() async {
    if (_url == null || _token == null) return;

    _setState(ConnectionState.connecting);

    try {
      final uri = Uri.parse('$_url?token=$_token');
      _channel = WebSocketChannel.connect(uri);
      await _channel!.ready;

      _setState(ConnectionState.connected);
      _reconnection.reset();
      _startHeartbeatMonitor();

      _channel!.stream.listen(
        _onMessage,
        onError: _onError,
        onDone: _onDone,
      );
    } catch (e) {
      _logger.e('WebSocket connection failed', error: e);
      _handleReconnection();
    }
  }

  /// Gracefully disconnect.
  Future<void> disconnect() async {
    _heartbeatTimer?.cancel();
    await _channel?.sink.close();
    _channel = null;
    _setState(ConnectionState.disconnected);
  }

  /// Reconnect with a new token (e.g. after token refresh).
  Future<void> reconnectWithToken(String token) async {
    _token = token;
    await disconnect();
    await _doConnect();
  }

  void _onMessage(dynamic data) {
    _resetHeartbeatTimer();

    try {
      final json = jsonDecode(data as String) as Map<String, dynamic>;

      // The backend sends an `event_type` (or `type`) field in snake_case.
      // The Freezed-generated WebSocketEvent expects a `runtimeType` field
      // with camelCase values.  Normalize here.
      final backendType =
          json['event_type'] as String? ?? json['type'] as String? ?? '';
      final mappedType = _backendEventTypeMap[backendType] ?? backendType;
      json['runtimeType'] = mappedType;

      final event = WebSocketEvent.fromJson(json);
      _eventController.add(event);
    } catch (e) {
      _logger.w('Failed to parse WebSocket message', error: e);
    }
  }

  void _onError(Object error) {
    _logger.e('WebSocket error', error: error);
    _handleReconnection();
  }

  void _onDone() {
    _logger.i('WebSocket connection closed');
    _handleReconnection();
  }

  void _startHeartbeatMonitor() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer(_heartbeatTimeout, () {
      _logger.w('Heartbeat timeout -- reconnecting');
      _handleReconnection();
    });
  }

  void _resetHeartbeatTimer() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer(_heartbeatTimeout, () {
      _logger.w('Heartbeat timeout -- reconnecting');
      _handleReconnection();
    });
  }

  void _handleReconnection() {
    _heartbeatTimer?.cancel();
    _channel = null;
    _setState(ConnectionState.reconnecting);

    final delay = _reconnection.nextDelay;
    _logger.d(
      'Reconnecting in ${delay.inMilliseconds}ms '
      '(attempt ${_reconnection.attempts})',
    );

    Timer(delay, () => _doConnect());
  }

  void _setState(ConnectionState newState) {
    if (_state != newState) {
      _state = newState;
      _stateController.add(newState);
    }
  }

  /// Dispose all resources.
  void dispose() {
    _heartbeatTimer?.cancel();
    _channel?.sink.close();
    _eventController.close();
    _stateController.close();
  }
}
