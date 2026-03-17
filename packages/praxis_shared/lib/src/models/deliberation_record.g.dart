// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'deliberation_record.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$DeliberationRecordImpl _$$DeliberationRecordImplFromJson(
        Map<String, dynamic> json) =>
    _$DeliberationRecordImpl(
      id: json['id'] as String,
      sessionId: json['sessionId'] as String,
      type: $enumDecode(_$DeliberationTypeEnumMap, json['type']),
      summary: json['summary'] as String,
      reasoning: json['reasoning'] as String,
      principalId: json['principalId'] as String,
      principalName: json['principalName'] as String,
      createdAt: DateTime.parse(json['createdAt'] as String),
      hash: json['hash'] as String?,
      context: json['context'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$$DeliberationRecordImplToJson(
        _$DeliberationRecordImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'sessionId': instance.sessionId,
      'type': _$DeliberationTypeEnumMap[instance.type]!,
      'summary': instance.summary,
      'reasoning': instance.reasoning,
      'principalId': instance.principalId,
      'principalName': instance.principalName,
      'createdAt': instance.createdAt.toIso8601String(),
      'hash': instance.hash,
      'context': instance.context,
    };

const _$DeliberationTypeEnumMap = {
  DeliberationType.decision: 'decision',
  DeliberationType.observation: 'observation',
  DeliberationType.question: 'question',
  DeliberationType.constraintChange: 'constraint_change',
  DeliberationType.approval: 'approval',
  DeliberationType.denial: 'denial',
};

_$DecisionDataImpl _$$DecisionDataImplFromJson(Map<String, dynamic> json) =>
    _$DecisionDataImpl(
      summary: json['summary'] as String,
      reasoning: json['reasoning'] as String,
      context: json['context'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$$DecisionDataImplToJson(_$DecisionDataImpl instance) =>
    <String, dynamic>{
      'summary': instance.summary,
      'reasoning': instance.reasoning,
      'context': instance.context,
    };
