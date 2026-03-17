// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'trust_entry.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$TrustEntryImpl _$$TrustEntryImplFromJson(Map<String, dynamic> json) =>
    _$TrustEntryImpl(
      id: json['id'] as String,
      sessionId: json['sessionId'] as String,
      type: $enumDecode(_$TrustEntryTypeEnumMap, json['type']),
      principalId: json['principalId'] as String,
      principalName: json['principalName'] as String,
      description: json['description'] as String,
      hash: json['hash'] as String,
      parentHash: json['parentHash'] as String?,
      verificationStatus:
          $enumDecode(_$VerificationStatusEnumMap, json['verificationStatus']),
      createdAt: DateTime.parse(json['createdAt'] as String),
      metadata: json['metadata'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$$TrustEntryImplToJson(_$TrustEntryImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'sessionId': instance.sessionId,
      'type': _$TrustEntryTypeEnumMap[instance.type]!,
      'principalId': instance.principalId,
      'principalName': instance.principalName,
      'description': instance.description,
      'hash': instance.hash,
      'parentHash': instance.parentHash,
      'verificationStatus':
          _$VerificationStatusEnumMap[instance.verificationStatus]!,
      'createdAt': instance.createdAt.toIso8601String(),
      'metadata': instance.metadata,
    };

const _$TrustEntryTypeEnumMap = {
  TrustEntryType.genesis: 'genesis',
  TrustEntryType.delegation: 'delegation',
  TrustEntryType.constraint: 'constraint',
  TrustEntryType.attestation: 'attestation',
  TrustEntryType.action: 'action',
  TrustEntryType.approval: 'approval',
};

const _$VerificationStatusEnumMap = {
  VerificationStatus.verified: 'verified',
  VerificationStatus.unverified: 'unverified',
  VerificationStatus.failed: 'failed',
};
