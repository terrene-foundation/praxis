import 'package:freezed_annotation/freezed_annotation.dart';

part 'held_action.freezed.dart';
part 'held_action.g.dart';

/// Status of a held action awaiting human decision.
enum HeldActionStatus {
  @JsonValue('pending')
  pending,
  @JsonValue('approved')
  approved,
  @JsonValue('denied')
  denied,
  @JsonValue('approved_with_conditions')
  approvedWithConditions,
  @JsonValue('expired')
  expired,
}

/// An AI action that was held by the constraint enforcer and requires human approval.
@freezed
class HeldAction with _$HeldAction {
  const factory HeldAction({
    required String id,
    required String sessionId,
    required String actionType,
    required String description,
    required String constraintTriggered,
    required String reasoning,
    required HeldActionStatus status,
    required DateTime createdAt,
    DateTime? resolvedAt,
    String? resolvedBy,
    String? conditions,
  }) = _HeldAction;

  factory HeldAction.fromJson(Map<String, dynamic> json) =>
      _$HeldActionFromJson(json);
}
