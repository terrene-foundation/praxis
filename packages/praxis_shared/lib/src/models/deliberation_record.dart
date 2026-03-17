import 'package:freezed_annotation/freezed_annotation.dart';

part 'deliberation_record.freezed.dart';
part 'deliberation_record.g.dart';

/// Type of deliberation captured during a CO session.
enum DeliberationType {
  @JsonValue('decision')
  decision,
  @JsonValue('observation')
  observation,
  @JsonValue('question')
  question,
  @JsonValue('constraint_change')
  constraintChange,
  @JsonValue('approval')
  approval,
  @JsonValue('denial')
  denial,
}

/// A captured record of human-AI deliberation within a session.
@freezed
class DeliberationRecord with _$DeliberationRecord {
  const factory DeliberationRecord({
    required String id,
    required String sessionId,
    required DeliberationType type,
    required String summary,
    required String reasoning,
    required String principalId,
    required String principalName,
    required DateTime createdAt,
    String? hash,
    Map<String, dynamic>? context,
  }) = _DeliberationRecord;

  factory DeliberationRecord.fromJson(Map<String, dynamic> json) =>
      _$DeliberationRecordFromJson(json);
}

/// Data for creating a new decision deliberation record.
@freezed
class DecisionData with _$DecisionData {
  const factory DecisionData({
    required String summary,
    required String reasoning,
    Map<String, dynamic>? context,
  }) = _DecisionData;

  factory DecisionData.fromJson(Map<String, dynamic> json) =>
      _$DecisionDataFromJson(json);
}
