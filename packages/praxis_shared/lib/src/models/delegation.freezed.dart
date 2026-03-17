// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'delegation.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

Delegation _$DelegationFromJson(Map<String, dynamic> json) {
  return _Delegation.fromJson(json);
}

/// @nodoc
mixin _$Delegation {
  String get id => throw _privateConstructorUsedError;
  String get delegatorId => throw _privateConstructorUsedError;
  String get delegateeId => throw _privateConstructorUsedError;
  String get delegatorName => throw _privateConstructorUsedError;
  String get delegateeName => throw _privateConstructorUsedError;
  ConstraintSet get constraints => throw _privateConstructorUsedError;
  DateTime get createdAt => throw _privateConstructorUsedError;
  DateTime? get revokedAt => throw _privateConstructorUsedError;
  bool get isActive => throw _privateConstructorUsedError;

  /// Serializes this Delegation to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of Delegation
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $DelegationCopyWith<Delegation> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DelegationCopyWith<$Res> {
  factory $DelegationCopyWith(
          Delegation value, $Res Function(Delegation) then) =
      _$DelegationCopyWithImpl<$Res, Delegation>;
  @useResult
  $Res call(
      {String id,
      String delegatorId,
      String delegateeId,
      String delegatorName,
      String delegateeName,
      ConstraintSet constraints,
      DateTime createdAt,
      DateTime? revokedAt,
      bool isActive});

  $ConstraintSetCopyWith<$Res> get constraints;
}

/// @nodoc
class _$DelegationCopyWithImpl<$Res, $Val extends Delegation>
    implements $DelegationCopyWith<$Res> {
  _$DelegationCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of Delegation
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? delegatorId = null,
    Object? delegateeId = null,
    Object? delegatorName = null,
    Object? delegateeName = null,
    Object? constraints = null,
    Object? createdAt = null,
    Object? revokedAt = freezed,
    Object? isActive = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      delegatorId: null == delegatorId
          ? _value.delegatorId
          : delegatorId // ignore: cast_nullable_to_non_nullable
              as String,
      delegateeId: null == delegateeId
          ? _value.delegateeId
          : delegateeId // ignore: cast_nullable_to_non_nullable
              as String,
      delegatorName: null == delegatorName
          ? _value.delegatorName
          : delegatorName // ignore: cast_nullable_to_non_nullable
              as String,
      delegateeName: null == delegateeName
          ? _value.delegateeName
          : delegateeName // ignore: cast_nullable_to_non_nullable
              as String,
      constraints: null == constraints
          ? _value.constraints
          : constraints // ignore: cast_nullable_to_non_nullable
              as ConstraintSet,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      revokedAt: freezed == revokedAt
          ? _value.revokedAt
          : revokedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      isActive: null == isActive
          ? _value.isActive
          : isActive // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }

  /// Create a copy of Delegation
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $ConstraintSetCopyWith<$Res> get constraints {
    return $ConstraintSetCopyWith<$Res>(_value.constraints, (value) {
      return _then(_value.copyWith(constraints: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$DelegationImplCopyWith<$Res>
    implements $DelegationCopyWith<$Res> {
  factory _$$DelegationImplCopyWith(
          _$DelegationImpl value, $Res Function(_$DelegationImpl) then) =
      __$$DelegationImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String delegatorId,
      String delegateeId,
      String delegatorName,
      String delegateeName,
      ConstraintSet constraints,
      DateTime createdAt,
      DateTime? revokedAt,
      bool isActive});

  @override
  $ConstraintSetCopyWith<$Res> get constraints;
}

/// @nodoc
class __$$DelegationImplCopyWithImpl<$Res>
    extends _$DelegationCopyWithImpl<$Res, _$DelegationImpl>
    implements _$$DelegationImplCopyWith<$Res> {
  __$$DelegationImplCopyWithImpl(
      _$DelegationImpl _value, $Res Function(_$DelegationImpl) _then)
      : super(_value, _then);

  /// Create a copy of Delegation
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? delegatorId = null,
    Object? delegateeId = null,
    Object? delegatorName = null,
    Object? delegateeName = null,
    Object? constraints = null,
    Object? createdAt = null,
    Object? revokedAt = freezed,
    Object? isActive = null,
  }) {
    return _then(_$DelegationImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      delegatorId: null == delegatorId
          ? _value.delegatorId
          : delegatorId // ignore: cast_nullable_to_non_nullable
              as String,
      delegateeId: null == delegateeId
          ? _value.delegateeId
          : delegateeId // ignore: cast_nullable_to_non_nullable
              as String,
      delegatorName: null == delegatorName
          ? _value.delegatorName
          : delegatorName // ignore: cast_nullable_to_non_nullable
              as String,
      delegateeName: null == delegateeName
          ? _value.delegateeName
          : delegateeName // ignore: cast_nullable_to_non_nullable
              as String,
      constraints: null == constraints
          ? _value.constraints
          : constraints // ignore: cast_nullable_to_non_nullable
              as ConstraintSet,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      revokedAt: freezed == revokedAt
          ? _value.revokedAt
          : revokedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      isActive: null == isActive
          ? _value.isActive
          : isActive // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$DelegationImpl implements _Delegation {
  const _$DelegationImpl(
      {required this.id,
      required this.delegatorId,
      required this.delegateeId,
      required this.delegatorName,
      required this.delegateeName,
      required this.constraints,
      required this.createdAt,
      this.revokedAt,
      required this.isActive});

  factory _$DelegationImpl.fromJson(Map<String, dynamic> json) =>
      _$$DelegationImplFromJson(json);

  @override
  final String id;
  @override
  final String delegatorId;
  @override
  final String delegateeId;
  @override
  final String delegatorName;
  @override
  final String delegateeName;
  @override
  final ConstraintSet constraints;
  @override
  final DateTime createdAt;
  @override
  final DateTime? revokedAt;
  @override
  final bool isActive;

  @override
  String toString() {
    return 'Delegation(id: $id, delegatorId: $delegatorId, delegateeId: $delegateeId, delegatorName: $delegatorName, delegateeName: $delegateeName, constraints: $constraints, createdAt: $createdAt, revokedAt: $revokedAt, isActive: $isActive)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DelegationImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.delegatorId, delegatorId) ||
                other.delegatorId == delegatorId) &&
            (identical(other.delegateeId, delegateeId) ||
                other.delegateeId == delegateeId) &&
            (identical(other.delegatorName, delegatorName) ||
                other.delegatorName == delegatorName) &&
            (identical(other.delegateeName, delegateeName) ||
                other.delegateeName == delegateeName) &&
            (identical(other.constraints, constraints) ||
                other.constraints == constraints) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt) &&
            (identical(other.revokedAt, revokedAt) ||
                other.revokedAt == revokedAt) &&
            (identical(other.isActive, isActive) ||
                other.isActive == isActive));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      delegatorId,
      delegateeId,
      delegatorName,
      delegateeName,
      constraints,
      createdAt,
      revokedAt,
      isActive);

  /// Create a copy of Delegation
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$DelegationImplCopyWith<_$DelegationImpl> get copyWith =>
      __$$DelegationImplCopyWithImpl<_$DelegationImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$DelegationImplToJson(
      this,
    );
  }
}

abstract class _Delegation implements Delegation {
  const factory _Delegation(
      {required final String id,
      required final String delegatorId,
      required final String delegateeId,
      required final String delegatorName,
      required final String delegateeName,
      required final ConstraintSet constraints,
      required final DateTime createdAt,
      final DateTime? revokedAt,
      required final bool isActive}) = _$DelegationImpl;

  factory _Delegation.fromJson(Map<String, dynamic> json) =
      _$DelegationImpl.fromJson;

  @override
  String get id;
  @override
  String get delegatorId;
  @override
  String get delegateeId;
  @override
  String get delegatorName;
  @override
  String get delegateeName;
  @override
  ConstraintSet get constraints;
  @override
  DateTime get createdAt;
  @override
  DateTime? get revokedAt;
  @override
  bool get isActive;

  /// Create a copy of Delegation
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$DelegationImplCopyWith<_$DelegationImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
