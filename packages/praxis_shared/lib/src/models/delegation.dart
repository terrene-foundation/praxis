import 'package:freezed_annotation/freezed_annotation.dart';

import 'constraint_set.dart';

part 'delegation.freezed.dart';
part 'delegation.g.dart';

/// A delegation of authority from one principal to another.
@freezed
class Delegation with _$Delegation {
  const factory Delegation({
    required String id,
    required String delegatorId,
    required String delegateeId,
    required String delegatorName,
    required String delegateeName,
    required ConstraintSet constraints,
    required DateTime createdAt,
    DateTime? revokedAt,
    required bool isActive,
  }) = _Delegation;

  factory Delegation.fromJson(Map<String, dynamic> json) =>
      _$DelegationFromJson(json);
}
