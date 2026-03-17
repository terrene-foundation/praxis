import 'package:freezed_annotation/freezed_annotation.dart';

part 'constraint_set.freezed.dart';
part 'constraint_set.g.dart';

/// The five constraint dimensions defined by CO methodology.
@freezed
class ConstraintSet with _$ConstraintSet {
  const factory ConstraintSet({
    required FinancialConstraint financial,
    required OperationalConstraint operational,
    required TemporalConstraint temporal,
    required DataAccessConstraint dataAccess,
    required CommunicationConstraint communication,
  }) = _ConstraintSet;

  factory ConstraintSet.fromJson(Map<String, dynamic> json) =>
      _$ConstraintSetFromJson(json);
}

/// Financial constraint dimension.
@freezed
class FinancialConstraint with _$FinancialConstraint {
  const factory FinancialConstraint({
    required double maxAmount,
    required double currentUsage,
    required String currency,
    @Default(false) bool requireApprovalAbove,
    double? approvalThreshold,
  }) = _FinancialConstraint;

  factory FinancialConstraint.fromJson(Map<String, dynamic> json) =>
      _$FinancialConstraintFromJson(json);
}

/// Operational constraint dimension.
@freezed
class OperationalConstraint with _$OperationalConstraint {
  const factory OperationalConstraint({
    required List<String> allowedActions,
    required List<String> blockedActions,
    @Default(false) bool requireApprovalForDestructive,
  }) = _OperationalConstraint;

  factory OperationalConstraint.fromJson(Map<String, dynamic> json) =>
      _$OperationalConstraintFromJson(json);
}

/// Temporal constraint dimension.
@freezed
class TemporalConstraint with _$TemporalConstraint {
  const factory TemporalConstraint({
    DateTime? validFrom,
    DateTime? validUntil,
    int? maxDurationMinutes,
    List<String>? allowedTimeWindows,
  }) = _TemporalConstraint;

  factory TemporalConstraint.fromJson(Map<String, dynamic> json) =>
      _$TemporalConstraintFromJson(json);
}

/// Data access constraint dimension.
@freezed
class DataAccessConstraint with _$DataAccessConstraint {
  const factory DataAccessConstraint({
    required List<String> allowedResources,
    required List<String> blockedResources,
    @Default('read') String defaultAccess,
    @Default(false) bool requireApprovalForWrite,
  }) = _DataAccessConstraint;

  factory DataAccessConstraint.fromJson(Map<String, dynamic> json) =>
      _$DataAccessConstraintFromJson(json);
}

/// Communication constraint dimension.
@freezed
class CommunicationConstraint with _$CommunicationConstraint {
  const factory CommunicationConstraint({
    required List<String> allowedChannels,
    required List<String> blockedChannels,
    @Default(false) bool requireApprovalForExternal,
  }) = _CommunicationConstraint;

  factory CommunicationConstraint.fromJson(Map<String, dynamic> json) =>
      _$CommunicationConstraintFromJson(json);
}

/// A constraint preset template.
@freezed
class ConstraintPreset with _$ConstraintPreset {
  const factory ConstraintPreset({
    required String id,
    required String name,
    required String description,
    required String domain,
    required ConstraintSet constraints,
  }) = _ConstraintPreset;

  factory ConstraintPreset.fromJson(Map<String, dynamic> json) =>
      _$ConstraintPresetFromJson(json);
}
