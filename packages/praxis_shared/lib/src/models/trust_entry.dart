import 'package:freezed_annotation/freezed_annotation.dart';

part 'trust_entry.freezed.dart';
part 'trust_entry.g.dart';

/// Type of trust chain entry.
enum TrustEntryType {
  @JsonValue('genesis')
  genesis,
  @JsonValue('delegation')
  delegation,
  @JsonValue('constraint')
  constraint,
  @JsonValue('attestation')
  attestation,
  @JsonValue('action')
  action,
  @JsonValue('approval')
  approval,
}

/// Verification status of a trust entry.
enum VerificationStatus {
  @JsonValue('verified')
  verified,
  @JsonValue('unverified')
  unverified,
  @JsonValue('failed')
  failed,
}

/// An entry in the EATP trust chain.
@freezed
class TrustEntry with _$TrustEntry {
  const factory TrustEntry({
    required String id,
    required String sessionId,
    required TrustEntryType type,
    required String principalId,
    required String principalName,
    required String description,
    required String hash,
    String? parentHash,
    required VerificationStatus verificationStatus,
    required DateTime createdAt,
    Map<String, dynamic>? metadata,
  }) = _TrustEntry;

  factory TrustEntry.fromJson(Map<String, dynamic> json) =>
      _$TrustEntryFromJson(json);
}
