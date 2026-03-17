// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'deliberation_record.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

DeliberationRecord _$DeliberationRecordFromJson(Map<String, dynamic> json) {
  return _DeliberationRecord.fromJson(json);
}

/// @nodoc
mixin _$DeliberationRecord {
  String get id => throw _privateConstructorUsedError;
  String get sessionId => throw _privateConstructorUsedError;
  DeliberationType get type => throw _privateConstructorUsedError;
  String get summary => throw _privateConstructorUsedError;
  String get reasoning => throw _privateConstructorUsedError;
  String get principalId => throw _privateConstructorUsedError;
  String get principalName => throw _privateConstructorUsedError;
  DateTime get createdAt => throw _privateConstructorUsedError;
  String? get hash => throw _privateConstructorUsedError;
  Map<String, dynamic>? get context => throw _privateConstructorUsedError;

  /// Serializes this DeliberationRecord to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of DeliberationRecord
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $DeliberationRecordCopyWith<DeliberationRecord> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DeliberationRecordCopyWith<$Res> {
  factory $DeliberationRecordCopyWith(
          DeliberationRecord value, $Res Function(DeliberationRecord) then) =
      _$DeliberationRecordCopyWithImpl<$Res, DeliberationRecord>;
  @useResult
  $Res call(
      {String id,
      String sessionId,
      DeliberationType type,
      String summary,
      String reasoning,
      String principalId,
      String principalName,
      DateTime createdAt,
      String? hash,
      Map<String, dynamic>? context});
}

/// @nodoc
class _$DeliberationRecordCopyWithImpl<$Res, $Val extends DeliberationRecord>
    implements $DeliberationRecordCopyWith<$Res> {
  _$DeliberationRecordCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of DeliberationRecord
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? sessionId = null,
    Object? type = null,
    Object? summary = null,
    Object? reasoning = null,
    Object? principalId = null,
    Object? principalName = null,
    Object? createdAt = null,
    Object? hash = freezed,
    Object? context = freezed,
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
              as DeliberationType,
      summary: null == summary
          ? _value.summary
          : summary // ignore: cast_nullable_to_non_nullable
              as String,
      reasoning: null == reasoning
          ? _value.reasoning
          : reasoning // ignore: cast_nullable_to_non_nullable
              as String,
      principalId: null == principalId
          ? _value.principalId
          : principalId // ignore: cast_nullable_to_non_nullable
              as String,
      principalName: null == principalName
          ? _value.principalName
          : principalName // ignore: cast_nullable_to_non_nullable
              as String,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      hash: freezed == hash
          ? _value.hash
          : hash // ignore: cast_nullable_to_non_nullable
              as String?,
      context: freezed == context
          ? _value.context
          : context // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$DeliberationRecordImplCopyWith<$Res>
    implements $DeliberationRecordCopyWith<$Res> {
  factory _$$DeliberationRecordImplCopyWith(_$DeliberationRecordImpl value,
          $Res Function(_$DeliberationRecordImpl) then) =
      __$$DeliberationRecordImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String sessionId,
      DeliberationType type,
      String summary,
      String reasoning,
      String principalId,
      String principalName,
      DateTime createdAt,
      String? hash,
      Map<String, dynamic>? context});
}

/// @nodoc
class __$$DeliberationRecordImplCopyWithImpl<$Res>
    extends _$DeliberationRecordCopyWithImpl<$Res, _$DeliberationRecordImpl>
    implements _$$DeliberationRecordImplCopyWith<$Res> {
  __$$DeliberationRecordImplCopyWithImpl(_$DeliberationRecordImpl _value,
      $Res Function(_$DeliberationRecordImpl) _then)
      : super(_value, _then);

  /// Create a copy of DeliberationRecord
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? sessionId = null,
    Object? type = null,
    Object? summary = null,
    Object? reasoning = null,
    Object? principalId = null,
    Object? principalName = null,
    Object? createdAt = null,
    Object? hash = freezed,
    Object? context = freezed,
  }) {
    return _then(_$DeliberationRecordImpl(
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
              as DeliberationType,
      summary: null == summary
          ? _value.summary
          : summary // ignore: cast_nullable_to_non_nullable
              as String,
      reasoning: null == reasoning
          ? _value.reasoning
          : reasoning // ignore: cast_nullable_to_non_nullable
              as String,
      principalId: null == principalId
          ? _value.principalId
          : principalId // ignore: cast_nullable_to_non_nullable
              as String,
      principalName: null == principalName
          ? _value.principalName
          : principalName // ignore: cast_nullable_to_non_nullable
              as String,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      hash: freezed == hash
          ? _value.hash
          : hash // ignore: cast_nullable_to_non_nullable
              as String?,
      context: freezed == context
          ? _value._context
          : context // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$DeliberationRecordImpl implements _DeliberationRecord {
  const _$DeliberationRecordImpl(
      {required this.id,
      required this.sessionId,
      required this.type,
      required this.summary,
      required this.reasoning,
      required this.principalId,
      required this.principalName,
      required this.createdAt,
      this.hash,
      final Map<String, dynamic>? context})
      : _context = context;

  factory _$DeliberationRecordImpl.fromJson(Map<String, dynamic> json) =>
      _$$DeliberationRecordImplFromJson(json);

  @override
  final String id;
  @override
  final String sessionId;
  @override
  final DeliberationType type;
  @override
  final String summary;
  @override
  final String reasoning;
  @override
  final String principalId;
  @override
  final String principalName;
  @override
  final DateTime createdAt;
  @override
  final String? hash;
  final Map<String, dynamic>? _context;
  @override
  Map<String, dynamic>? get context {
    final value = _context;
    if (value == null) return null;
    if (_context is EqualUnmodifiableMapView) return _context;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  @override
  String toString() {
    return 'DeliberationRecord(id: $id, sessionId: $sessionId, type: $type, summary: $summary, reasoning: $reasoning, principalId: $principalId, principalName: $principalName, createdAt: $createdAt, hash: $hash, context: $context)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DeliberationRecordImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.sessionId, sessionId) ||
                other.sessionId == sessionId) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.summary, summary) || other.summary == summary) &&
            (identical(other.reasoning, reasoning) ||
                other.reasoning == reasoning) &&
            (identical(other.principalId, principalId) ||
                other.principalId == principalId) &&
            (identical(other.principalName, principalName) ||
                other.principalName == principalName) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt) &&
            (identical(other.hash, hash) || other.hash == hash) &&
            const DeepCollectionEquality().equals(other._context, _context));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      sessionId,
      type,
      summary,
      reasoning,
      principalId,
      principalName,
      createdAt,
      hash,
      const DeepCollectionEquality().hash(_context));

  /// Create a copy of DeliberationRecord
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$DeliberationRecordImplCopyWith<_$DeliberationRecordImpl> get copyWith =>
      __$$DeliberationRecordImplCopyWithImpl<_$DeliberationRecordImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$DeliberationRecordImplToJson(
      this,
    );
  }
}

abstract class _DeliberationRecord implements DeliberationRecord {
  const factory _DeliberationRecord(
      {required final String id,
      required final String sessionId,
      required final DeliberationType type,
      required final String summary,
      required final String reasoning,
      required final String principalId,
      required final String principalName,
      required final DateTime createdAt,
      final String? hash,
      final Map<String, dynamic>? context}) = _$DeliberationRecordImpl;

  factory _DeliberationRecord.fromJson(Map<String, dynamic> json) =
      _$DeliberationRecordImpl.fromJson;

  @override
  String get id;
  @override
  String get sessionId;
  @override
  DeliberationType get type;
  @override
  String get summary;
  @override
  String get reasoning;
  @override
  String get principalId;
  @override
  String get principalName;
  @override
  DateTime get createdAt;
  @override
  String? get hash;
  @override
  Map<String, dynamic>? get context;

  /// Create a copy of DeliberationRecord
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$DeliberationRecordImplCopyWith<_$DeliberationRecordImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

DecisionData _$DecisionDataFromJson(Map<String, dynamic> json) {
  return _DecisionData.fromJson(json);
}

/// @nodoc
mixin _$DecisionData {
  String get summary => throw _privateConstructorUsedError;
  String get reasoning => throw _privateConstructorUsedError;
  Map<String, dynamic>? get context => throw _privateConstructorUsedError;

  /// Serializes this DecisionData to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of DecisionData
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $DecisionDataCopyWith<DecisionData> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DecisionDataCopyWith<$Res> {
  factory $DecisionDataCopyWith(
          DecisionData value, $Res Function(DecisionData) then) =
      _$DecisionDataCopyWithImpl<$Res, DecisionData>;
  @useResult
  $Res call({String summary, String reasoning, Map<String, dynamic>? context});
}

/// @nodoc
class _$DecisionDataCopyWithImpl<$Res, $Val extends DecisionData>
    implements $DecisionDataCopyWith<$Res> {
  _$DecisionDataCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of DecisionData
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? summary = null,
    Object? reasoning = null,
    Object? context = freezed,
  }) {
    return _then(_value.copyWith(
      summary: null == summary
          ? _value.summary
          : summary // ignore: cast_nullable_to_non_nullable
              as String,
      reasoning: null == reasoning
          ? _value.reasoning
          : reasoning // ignore: cast_nullable_to_non_nullable
              as String,
      context: freezed == context
          ? _value.context
          : context // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$DecisionDataImplCopyWith<$Res>
    implements $DecisionDataCopyWith<$Res> {
  factory _$$DecisionDataImplCopyWith(
          _$DecisionDataImpl value, $Res Function(_$DecisionDataImpl) then) =
      __$$DecisionDataImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String summary, String reasoning, Map<String, dynamic>? context});
}

/// @nodoc
class __$$DecisionDataImplCopyWithImpl<$Res>
    extends _$DecisionDataCopyWithImpl<$Res, _$DecisionDataImpl>
    implements _$$DecisionDataImplCopyWith<$Res> {
  __$$DecisionDataImplCopyWithImpl(
      _$DecisionDataImpl _value, $Res Function(_$DecisionDataImpl) _then)
      : super(_value, _then);

  /// Create a copy of DecisionData
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? summary = null,
    Object? reasoning = null,
    Object? context = freezed,
  }) {
    return _then(_$DecisionDataImpl(
      summary: null == summary
          ? _value.summary
          : summary // ignore: cast_nullable_to_non_nullable
              as String,
      reasoning: null == reasoning
          ? _value.reasoning
          : reasoning // ignore: cast_nullable_to_non_nullable
              as String,
      context: freezed == context
          ? _value._context
          : context // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$DecisionDataImpl implements _DecisionData {
  const _$DecisionDataImpl(
      {required this.summary,
      required this.reasoning,
      final Map<String, dynamic>? context})
      : _context = context;

  factory _$DecisionDataImpl.fromJson(Map<String, dynamic> json) =>
      _$$DecisionDataImplFromJson(json);

  @override
  final String summary;
  @override
  final String reasoning;
  final Map<String, dynamic>? _context;
  @override
  Map<String, dynamic>? get context {
    final value = _context;
    if (value == null) return null;
    if (_context is EqualUnmodifiableMapView) return _context;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  @override
  String toString() {
    return 'DecisionData(summary: $summary, reasoning: $reasoning, context: $context)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DecisionDataImpl &&
            (identical(other.summary, summary) || other.summary == summary) &&
            (identical(other.reasoning, reasoning) ||
                other.reasoning == reasoning) &&
            const DeepCollectionEquality().equals(other._context, _context));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, summary, reasoning,
      const DeepCollectionEquality().hash(_context));

  /// Create a copy of DecisionData
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$DecisionDataImplCopyWith<_$DecisionDataImpl> get copyWith =>
      __$$DecisionDataImplCopyWithImpl<_$DecisionDataImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$DecisionDataImplToJson(
      this,
    );
  }
}

abstract class _DecisionData implements DecisionData {
  const factory _DecisionData(
      {required final String summary,
      required final String reasoning,
      final Map<String, dynamic>? context}) = _$DecisionDataImpl;

  factory _DecisionData.fromJson(Map<String, dynamic> json) =
      _$DecisionDataImpl.fromJson;

  @override
  String get summary;
  @override
  String get reasoning;
  @override
  Map<String, dynamic>? get context;

  /// Create a copy of DecisionData
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$DecisionDataImplCopyWith<_$DecisionDataImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
