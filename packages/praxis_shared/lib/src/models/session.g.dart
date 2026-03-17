// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'session.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$SessionImpl _$$SessionImplFromJson(Map<String, dynamic> json) =>
    _$SessionImpl(
      id: json['id'] as String,
      name: json['name'] as String,
      domain: json['domain'] as String,
      status: $enumDecode(_$SessionStatusEnumMap, json['status']),
      constraints:
          ConstraintSet.fromJson(json['constraints'] as Map<String, dynamic>),
      createdAt: DateTime.parse(json['createdAt'] as String),
      endedAt: json['endedAt'] == null
          ? null
          : DateTime.parse(json['endedAt'] as String),
      createdBy: json['createdBy'] as String,
      workspaceId: json['workspaceId'] as String?,
      description: json['description'] as String?,
    );

Map<String, dynamic> _$$SessionImplToJson(_$SessionImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'domain': instance.domain,
      'status': _$SessionStatusEnumMap[instance.status]!,
      'constraints': instance.constraints,
      'createdAt': instance.createdAt.toIso8601String(),
      'endedAt': instance.endedAt?.toIso8601String(),
      'createdBy': instance.createdBy,
      'workspaceId': instance.workspaceId,
      'description': instance.description,
    };

const _$SessionStatusEnumMap = {
  SessionStatus.active: 'active',
  SessionStatus.paused: 'paused',
  SessionStatus.ended: 'ended',
};

_$CreateSessionRequestImpl _$$CreateSessionRequestImplFromJson(
        Map<String, dynamic> json) =>
    _$CreateSessionRequestImpl(
      name: json['name'] as String,
      domain: json['domain'] as String,
      workspaceId: json['workspaceId'] as String?,
      description: json['description'] as String?,
      constraints: json['constraints'] == null
          ? null
          : ConstraintSet.fromJson(json['constraints'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$CreateSessionRequestImplToJson(
        _$CreateSessionRequestImpl instance) =>
    <String, dynamic>{
      'name': instance.name,
      'domain': instance.domain,
      'workspaceId': instance.workspaceId,
      'description': instance.description,
      'constraints': instance.constraints,
    };
