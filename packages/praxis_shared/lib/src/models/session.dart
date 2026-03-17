import 'package:freezed_annotation/freezed_annotation.dart';

import 'constraint_set.dart';

part 'session.freezed.dart';
part 'session.g.dart';

/// Status of a CO session.
enum SessionStatus {
  @JsonValue('active')
  active,
  @JsonValue('paused')
  paused,
  @JsonValue('ended')
  ended,
}

/// A Praxis CO collaboration session.
@freezed
class Session with _$Session {
  const factory Session({
    required String id,
    required String name,
    required String domain,
    required SessionStatus status,
    required ConstraintSet constraints,
    required DateTime createdAt,
    DateTime? endedAt,
    required String createdBy,
    String? workspaceId,
    String? description,
  }) = _Session;

  factory Session.fromJson(Map<String, dynamic> json) =>
      _$SessionFromJson(json);
}

/// Request to create a new session.
@freezed
class CreateSessionRequest with _$CreateSessionRequest {
  const factory CreateSessionRequest({
    required String name,
    required String domain,
    String? workspaceId,
    String? description,
    ConstraintSet? constraints,
  }) = _CreateSessionRequest;

  factory CreateSessionRequest.fromJson(Map<String, dynamic> json) =>
      _$CreateSessionRequestFromJson(json);
}
