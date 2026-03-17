// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'constraint_set.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$ConstraintSetImpl _$$ConstraintSetImplFromJson(Map<String, dynamic> json) =>
    _$ConstraintSetImpl(
      financial: FinancialConstraint.fromJson(
          json['financial'] as Map<String, dynamic>),
      operational: OperationalConstraint.fromJson(
          json['operational'] as Map<String, dynamic>),
      temporal:
          TemporalConstraint.fromJson(json['temporal'] as Map<String, dynamic>),
      dataAccess: DataAccessConstraint.fromJson(
          json['dataAccess'] as Map<String, dynamic>),
      communication: CommunicationConstraint.fromJson(
          json['communication'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$ConstraintSetImplToJson(_$ConstraintSetImpl instance) =>
    <String, dynamic>{
      'financial': instance.financial,
      'operational': instance.operational,
      'temporal': instance.temporal,
      'dataAccess': instance.dataAccess,
      'communication': instance.communication,
    };

_$FinancialConstraintImpl _$$FinancialConstraintImplFromJson(
        Map<String, dynamic> json) =>
    _$FinancialConstraintImpl(
      maxAmount: (json['maxAmount'] as num).toDouble(),
      currentUsage: (json['currentUsage'] as num).toDouble(),
      currency: json['currency'] as String,
      requireApprovalAbove: json['requireApprovalAbove'] as bool? ?? false,
      approvalThreshold: (json['approvalThreshold'] as num?)?.toDouble(),
    );

Map<String, dynamic> _$$FinancialConstraintImplToJson(
        _$FinancialConstraintImpl instance) =>
    <String, dynamic>{
      'maxAmount': instance.maxAmount,
      'currentUsage': instance.currentUsage,
      'currency': instance.currency,
      'requireApprovalAbove': instance.requireApprovalAbove,
      'approvalThreshold': instance.approvalThreshold,
    };

_$OperationalConstraintImpl _$$OperationalConstraintImplFromJson(
        Map<String, dynamic> json) =>
    _$OperationalConstraintImpl(
      allowedActions: (json['allowedActions'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      blockedActions: (json['blockedActions'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      requireApprovalForDestructive:
          json['requireApprovalForDestructive'] as bool? ?? false,
    );

Map<String, dynamic> _$$OperationalConstraintImplToJson(
        _$OperationalConstraintImpl instance) =>
    <String, dynamic>{
      'allowedActions': instance.allowedActions,
      'blockedActions': instance.blockedActions,
      'requireApprovalForDestructive': instance.requireApprovalForDestructive,
    };

_$TemporalConstraintImpl _$$TemporalConstraintImplFromJson(
        Map<String, dynamic> json) =>
    _$TemporalConstraintImpl(
      validFrom: json['validFrom'] == null
          ? null
          : DateTime.parse(json['validFrom'] as String),
      validUntil: json['validUntil'] == null
          ? null
          : DateTime.parse(json['validUntil'] as String),
      maxDurationMinutes: (json['maxDurationMinutes'] as num?)?.toInt(),
      allowedTimeWindows: (json['allowedTimeWindows'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
    );

Map<String, dynamic> _$$TemporalConstraintImplToJson(
        _$TemporalConstraintImpl instance) =>
    <String, dynamic>{
      'validFrom': instance.validFrom?.toIso8601String(),
      'validUntil': instance.validUntil?.toIso8601String(),
      'maxDurationMinutes': instance.maxDurationMinutes,
      'allowedTimeWindows': instance.allowedTimeWindows,
    };

_$DataAccessConstraintImpl _$$DataAccessConstraintImplFromJson(
        Map<String, dynamic> json) =>
    _$DataAccessConstraintImpl(
      allowedResources: (json['allowedResources'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      blockedResources: (json['blockedResources'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      defaultAccess: json['defaultAccess'] as String? ?? 'read',
      requireApprovalForWrite:
          json['requireApprovalForWrite'] as bool? ?? false,
    );

Map<String, dynamic> _$$DataAccessConstraintImplToJson(
        _$DataAccessConstraintImpl instance) =>
    <String, dynamic>{
      'allowedResources': instance.allowedResources,
      'blockedResources': instance.blockedResources,
      'defaultAccess': instance.defaultAccess,
      'requireApprovalForWrite': instance.requireApprovalForWrite,
    };

_$CommunicationConstraintImpl _$$CommunicationConstraintImplFromJson(
        Map<String, dynamic> json) =>
    _$CommunicationConstraintImpl(
      allowedChannels: (json['allowedChannels'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      blockedChannels: (json['blockedChannels'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      requireApprovalForExternal:
          json['requireApprovalForExternal'] as bool? ?? false,
    );

Map<String, dynamic> _$$CommunicationConstraintImplToJson(
        _$CommunicationConstraintImpl instance) =>
    <String, dynamic>{
      'allowedChannels': instance.allowedChannels,
      'blockedChannels': instance.blockedChannels,
      'requireApprovalForExternal': instance.requireApprovalForExternal,
    };

_$ConstraintPresetImpl _$$ConstraintPresetImplFromJson(
        Map<String, dynamic> json) =>
    _$ConstraintPresetImpl(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String,
      domain: json['domain'] as String,
      constraints:
          ConstraintSet.fromJson(json['constraints'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$ConstraintPresetImplToJson(
        _$ConstraintPresetImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'description': instance.description,
      'domain': instance.domain,
      'constraints': instance.constraints,
    };
