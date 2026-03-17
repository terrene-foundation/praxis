// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'delegation.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$DelegationImpl _$$DelegationImplFromJson(Map<String, dynamic> json) =>
    _$DelegationImpl(
      id: json['id'] as String,
      delegatorId: json['delegatorId'] as String,
      delegateeId: json['delegateeId'] as String,
      delegatorName: json['delegatorName'] as String,
      delegateeName: json['delegateeName'] as String,
      constraints:
          ConstraintSet.fromJson(json['constraints'] as Map<String, dynamic>),
      createdAt: DateTime.parse(json['createdAt'] as String),
      revokedAt: json['revokedAt'] == null
          ? null
          : DateTime.parse(json['revokedAt'] as String),
      isActive: json['isActive'] as bool,
    );

Map<String, dynamic> _$$DelegationImplToJson(_$DelegationImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'delegatorId': instance.delegatorId,
      'delegateeId': instance.delegateeId,
      'delegatorName': instance.delegatorName,
      'delegateeName': instance.delegateeName,
      'constraints': instance.constraints,
      'createdAt': instance.createdAt.toIso8601String(),
      'revokedAt': instance.revokedAt?.toIso8601String(),
      'isActive': instance.isActive,
    };
