// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'held_action.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$HeldActionImpl _$$HeldActionImplFromJson(Map<String, dynamic> json) =>
    _$HeldActionImpl(
      id: json['id'] as String,
      sessionId: json['sessionId'] as String,
      actionType: json['actionType'] as String,
      description: json['description'] as String,
      constraintTriggered: json['constraintTriggered'] as String,
      reasoning: json['reasoning'] as String,
      status: $enumDecode(_$HeldActionStatusEnumMap, json['status']),
      createdAt: DateTime.parse(json['createdAt'] as String),
      resolvedAt: json['resolvedAt'] == null
          ? null
          : DateTime.parse(json['resolvedAt'] as String),
      resolvedBy: json['resolvedBy'] as String?,
      conditions: json['conditions'] as String?,
    );

Map<String, dynamic> _$$HeldActionImplToJson(_$HeldActionImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'sessionId': instance.sessionId,
      'actionType': instance.actionType,
      'description': instance.description,
      'constraintTriggered': instance.constraintTriggered,
      'reasoning': instance.reasoning,
      'status': _$HeldActionStatusEnumMap[instance.status]!,
      'createdAt': instance.createdAt.toIso8601String(),
      'resolvedAt': instance.resolvedAt?.toIso8601String(),
      'resolvedBy': instance.resolvedBy,
      'conditions': instance.conditions,
    };

const _$HeldActionStatusEnumMap = {
  HeldActionStatus.pending: 'pending',
  HeldActionStatus.approved: 'approved',
  HeldActionStatus.denied: 'denied',
  HeldActionStatus.approvedWithConditions: 'approved_with_conditions',
  HeldActionStatus.expired: 'expired',
};
