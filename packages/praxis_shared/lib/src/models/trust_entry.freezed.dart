// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'trust_entry.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

TrustEntry _$TrustEntryFromJson(Map<String, dynamic> json) {
  return _TrustEntry.fromJson(json);
}

/// @nodoc
mixin _$TrustEntry {
  String get id => throw _privateConstructorUsedError;
  String get sessionId => throw _privateConstructorUsedError;
  TrustEntryType get type => throw _privateConstructorUsedError;
  String get principalId => throw _privateConstructorUsedError;
  String get principalName => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  String get hash => throw _privateConstructorUsedError;
  String? get parentHash => throw _privateConstructorUsedError;
  VerificationStatus get verificationStatus =>
      throw _privateConstructorUsedError;
  DateTime get createdAt => throw _privateConstructorUsedError;
  Map<String, dynamic>? get metadata => throw _privateConstructorUsedError;

  /// Serializes this TrustEntry to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of TrustEntry
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $TrustEntryCopyWith<TrustEntry> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $TrustEntryCopyWith<$Res> {
  factory $TrustEntryCopyWith(
          TrustEntry value, $Res Function(TrustEntry) then) =
      _$TrustEntryCopyWithImpl<$Res, TrustEntry>;
  @useResult
  $Res call(
      {String id,
      String sessionId,
      TrustEntryType type,
      String principalId,
      String principalName,
      String description,
      String hash,
      String? parentHash,
      VerificationStatus verificationStatus,
      DateTime createdAt,
      Map<String, dynamic>? metadata});
}

/// @nodoc
class _$TrustEntryCopyWithImpl<$Res, $Val extends TrustEntry>
    implements $TrustEntryCopyWith<$Res> {
  _$TrustEntryCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of TrustEntry
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? sessionId = null,
    Object? type = null,
    Object? principalId = null,
    Object? principalName = null,
    Object? description = null,
    Object? hash = null,
    Object? parentHash = freezed,
    Object? verificationStatus = null,
    Object? createdAt = null,
    Object? metadata = freezed,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      sessionId: null == sessionId
          ? _value.sessionId
          : sessionId // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as TrustEntryType,
      principalId: null == principalId
          ? _value.principalId
          : principalId // ignore: cast_nullable_to_non_nullable
              as String,
      principalName: null == principalName
          ? _value.principalName
          : principalName // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      hash: null == hash
          ? _value.hash
          : hash // ignore: cast_nullable_to_non_nullable
              as String,
      parentHash: freezed == parentHash
          ? _value.parentHash
          : parentHash // ignore: cast_nullable_to_non_nullable
              as String?,
      verificationStatus: null == verificationStatus
          ? _value.verificationStatus
          : verificationStatus // ignore: cast_nullable_to_non_nullable
              as VerificationStatus,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      metadata: freezed == metadata
          ? _value.metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$TrustEntryImplCopyWith<$Res>
    implements $TrustEntryCopyWith<$Res> {
  factory _$$TrustEntryImplCopyWith(
          _$TrustEntryImpl value, $Res Function(_$TrustEntryImpl) then) =
      __$$TrustEntryImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String sessionId,
      TrustEntryType type,
      String principalId,
      String principalName,
      String description,
      String hash,
      String? parentHash,
      VerificationStatus verificationStatus,
      DateTime createdAt,
      Map<String, dynamic>? metadata});
}

/// @nodoc
class __$$TrustEntryImplCopyWithImpl<$Res>
    extends _$TrustEntryCopyWithImpl<$Res, _$TrustEntryImpl>
    implements _$$TrustEntryImplCopyWith<$Res> {
  __$$TrustEntryImplCopyWithImpl(
      _$TrustEntryImpl _value, $Res Function(_$TrustEntryImpl) _then)
      : super(_value, _then);

  /// Create a copy of TrustEntry
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? sessionId = null,
    Object? type = null,
    Object? principalId = null,
    Object? principalName = null,
    Object? description = null,
    Object? hash = null,
    Object? parentHash = freezed,
    Object? verificationStatus = null,
    Object? createdAt = null,
    Object? metadata = freezed,
  }) {
    return _then(_$TrustEntryImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      sessionId: null == sessionId
          ? _value.sessionId
          : sessionId // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as TrustEntryType,
      principalId: null == principalId
          ? _value.principalId
          : principalId // ignore: cast_nullable_to_non_nullable
              as String,
      principalName: null == principalName
          ? _value.principalName
          : principalName // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      hash: null == hash
          ? _value.hash
          : hash // ignore: cast_nullable_to_non_nullable
              as String,
      parentHash: freezed == parentHash
          ? _value.parentHash
          : parentHash // ignore: cast_nullable_to_non_nullable
              as String?,
      verificationStatus: null == verificationStatus
          ? _value.verificationStatus
          : verificationStatus // ignore: cast_nullable_to_non_nullable
              as VerificationStatus,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      metadata: freezed == metadata
          ? _value._metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$TrustEntryImpl implements _TrustEntry {
  const _$TrustEntryImpl(
      {required this.id,
      required this.sessionId,
      required this.type,
      required this.principalId,
      required this.principalName,
      required this.description,
      required this.hash,
      this.parentHash,
      required this.verificationStatus,
      required this.createdAt,
      final Map<String, dynamic>? metadata})
      : _metadata = metadata;

  factory _$TrustEntryImpl.fromJson(Map<String, dynamic> json) =>
      _$$TrustEntryImplFromJson(json);

  @override
  final String id;
  @override
  final String sessionId;
  @override
  final TrustEntryType type;
  @override
  final String principalId;
  @override
  final String principalName;
  @override
  final String description;
  @override
  final String hash;
  @override
  final String? parentHash;
  @override
  final VerificationStatus verificationStatus;
  @override
  final DateTime createdAt;
  final Map<String, dynamic>? _metadata;
  @override
  Map<String, dynamic>? get metadata {
    final value = _metadata;
    if (value == null) return null;
    if (_metadata is EqualUnmodifiableMapView) return _metadata;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  @override
  String toString() {
    return 'TrustEntry(id: $id, sessionId: $sessionId, type: $type, principalId: $principalId, principalName: $principalName, description: $description, hash: $hash, parentHash: $parentHash, verificationStatus: $verificationStatus, createdAt: $createdAt, metadata: $metadata)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$TrustEntryImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.sessionId, sessionId) ||
                other.sessionId == sessionId) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.principalId, principalId) ||
                other.principalId == principalId) &&
            (identical(other.principalName, principalName) ||
                other.principalName == principalName) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.hash, hash) || other.hash == hash) &&
            (identical(other.parentHash, parentHash) ||
                other.parentHash == parentHash) &&
            (identical(other.verificationStatus, verificationStatus) ||
                other.verificationStatus == verificationStatus) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt) &&
            const DeepCollectionEquality().equals(other._metadata, _metadata));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      sessionId,
      type,
      principalId,
      principalName,
      description,
      hash,
      parentHash,
      verificationStatus,
      createdAt,
      const DeepCollectionEquality().hash(_metadata));

  /// Create a copy of TrustEntry
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$TrustEntryImplCopyWith<_$TrustEntryImpl> get copyWith =>
      __$$TrustEntryImplCopyWithImpl<_$TrustEntryImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$TrustEntryImplToJson(
      this,
    );
  }
}

abstract class _TrustEntry implements TrustEntry {
  const factory _TrustEntry(
      {required final String id,
      required final String sessionId,
      required final TrustEntryType type,
      required final String principalId,
      required final String principalName,
      required final String description,
      required final String hash,
      final String? parentHash,
      required final VerificationStatus verificationStatus,
      required final DateTime createdAt,
      final Map<String, dynamic>? metadata}) = _$TrustEntryImpl;

  factory _TrustEntry.fromJson(Map<String, dynamic> json) =
      _$TrustEntryImpl.fromJson;

  @override
  String get id;
  @override
  String get sessionId;
  @override
  TrustEntryType get type;
  @override
  String get principalId;
  @override
  String get principalName;
  @override
  String get description;
  @override
  String get hash;
  @override
  String? get parentHash;
  @override
  VerificationStatus get verificationStatus;
  @override
  DateTime get createdAt;
  @override
  Map<String, dynamic>? get metadata;

  /// Create a copy of TrustEntry
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$TrustEntryImplCopyWith<_$TrustEntryImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
