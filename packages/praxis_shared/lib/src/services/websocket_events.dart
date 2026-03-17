import 'package:freezed_annotation/freezed_annotation.dart';

import '../models/constraint_set.dart';
import '../models/held_action.dart';
import '../models/session.dart';
import '../models/trust_entry.dart';

part 'websocket_events.freezed.dart';
part 'websocket_events.g.dart';

/// All real-time events delivered over the WebSocket connection.
@freezed
class WebSocketEvent with _$WebSocketEvent {
  // Session events
  const factory WebSocketEvent.sessionCreated(Session session) =
      SessionCreatedEvent;
  const factory WebSocketEvent.sessionUpdated(Session session) =
      SessionUpdatedEvent;
  const factory WebSocketEvent.sessionEnded(String sessionId) =
      SessionEndedEvent;

  // Constraint events
  const factory WebSocketEvent.constraintUpdated({
    required String sessionId,
    required ConstraintSet constraints,
  }) = ConstraintUpdatedEvent;
  const factory WebSocketEvent.constraintViolation({
    required String sessionId,
    required String dimension,
    required String description,
  }) = ConstraintViolationEvent;

  // Approval events
  const factory WebSocketEvent.actionHeld(HeldAction action) =
      ActionHeldEvent;
  const factory WebSocketEvent.actionResolved(HeldAction action) =
      ActionResolvedEvent;

  // Trust events
  const factory WebSocketEvent.trustEntryAdded({
    required String sessionId,
    required TrustEntry entry,
  }) = TrustEntryAddedEvent;

  // System events
  const factory WebSocketEvent.heartbeat() = HeartbeatEvent;
  const factory WebSocketEvent.error({required String message}) = ErrorEvent;

  factory WebSocketEvent.fromJson(Map<String, dynamic> json) =>
      _$WebSocketEventFromJson(json);
}
