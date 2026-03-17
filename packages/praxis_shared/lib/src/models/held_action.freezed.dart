// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'held_action.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

HeldAction _$HeldActionFromJson(Map<String, dynamic> json) {
  return _HeldAction.fromJson(json);
}

/// @nodoc
mixin _$HeldAction {
  String get id => throw _privateConstructorUsedError;
  String get sessionId => throw _privateConstructorUsedError;
  String get actionType => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  String get constraintTriggered => throw _privateConstructorUsedError;
  String get reasoning => throw _privateConstructorUsedError;
  HeldActionStatus get status => throw _privateConstructorUsedError;
  DateTime get createdAt => throw _privateConstructorUsedError;
  DateTime? get resolvedAt => throw _privateConstructorUsedError;
  String? get resolvedBy => throw _privateConstructorUsedError;
  String? get conditions => throw _privateConstructorUsedError;

  /// Serializes this HeldAction to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of HeldAction
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $HeldActionCopyWith<HeldAction> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HeldActionCopyWith<$Res> {
  factory $HeldActionCopyWith(
          HeldAction value, $Res Function(HeldAction) then) =
      _$HeldActionCopyWithImpl<$Res, HeldAction>;
  @useResult
  $Res call(
      {String id,
      String sessionId,
      String actionType,
      String description,
      String constraintTriggered,
      String reasoning,
      HeldActionStatus status,
      DateTime createdAt,
      DateTime? resolvedAt,
      String? resolvedBy,
      String? conditions});
}

/// @nodoc
class _$HeldActionCopyWithImpl<$Res, $Val extends HeldAction>
    implements $HeldActionCopyWith<$Res> {
  _$HeldActionCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of HeldAction
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? sessionId = null,
    Object? actionType = null,
    Object? description = null,
    Object? constraintTriggered = null,
    Object? reasoning = null,
    Object? status = null,
    Object? createdAt = null,
    Object? resolvedAt = freezed,
    Object? resolvedBy = freezed,
    Object? conditions = freezed,
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
      actionType: null == actionType
          ? _value.actionType
          : actionType // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      constraintTriggered: null == constraintTriggered
          ? _value.constraintTriggered
          : constraintTriggered // ignore: cast_nullable_to_non_nullable
              as String,
      reasoning: null == reasoning
          ? _value.reasoning
          : reasoning // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as HeldActionStatus,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      resolvedAt: freezed == resolvedAt
          ? _value.resolvedAt
          : resolvedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      resolvedBy: freezed == resolvedBy
          ? _value.resolvedBy
          : resolvedBy // ignore: cast_nullable_to_non_nullable
              as String?,
      conditions: freezed == conditions
          ? _value.conditions
          : conditions // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$HeldActionImplCopyWith<$Res>
    implements $HeldActionCopyWith<$Res> {
  factory _$$HeldActionImplCopyWith(
          _$HeldActionImpl value, $Res Function(_$HeldActionImpl) then) =
      __$$HeldActionImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String sessionId,
      String actionType,
      String description,
      String constraintTriggered,
      String reasoning,
      HeldActionStatus status,
      DateTime createdAt,
      DateTime? resolvedAt,
      String? resolvedBy,
      String? conditions});
}

/// @nodoc
class __$$HeldActionImplCopyWithImpl<$Res>
    extends _$HeldActionCopyWithImpl<$Res, _$HeldActionImpl>
    implements _$$HeldActionImplCopyWith<$Res> {
  __$$HeldActionImplCopyWithImpl(
      _$HeldActionImpl _value, $Res Function(_$HeldActionImpl) _then)
      : super(_value, _then);

  /// Create a copy of HeldAction
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? sessionId = null,
    Object? actionType = null,
    Object? description = null,
    Object? constraintTriggered = null,
    Object? reasoning = null,
    Object? status = null,
    Object? createdAt = null,
    Object? resolvedAt = freezed,
    Object? resolvedBy = freezed,
    Object? conditions = freezed,
  }) {
    return _then(_$HeldActionImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      sessionId: null == sessionId
          ? _value.sessionId
          : sessionId // ignore: cast_nullable_to_non_nullable
              as String,
      actionType: null == actionType
          ? _value.actionType
          : actionType // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      constraintTriggered: null == constraintTriggered
          ? _value.constraintTriggered
          : constraintTriggered // ignore: cast_nullable_to_non_nullable
              as String,
      reasoning: null == reasoning
          ? _value.reasoning
          : reasoning // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as HeldActionStatus,
      createdAt: null == createdAt
          ? _value.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      resolvedAt: freezed == resolvedAt
          ? _value.resolvedAt
          : resolvedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      resolvedBy: freezed == resolvedBy
          ? _value.resolvedBy
          : resolvedBy // ignore: cast_nullable_to_non_nullable
              as String?,
      conditions: freezed == conditions
          ? _value.conditions
          : conditions // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$HeldActionImpl implements _HeldAction {
  const _$HeldActionImpl(
      {required this.id,
      required this.sessionId,
      required this.actionType,
      required this.description,
      required this.constraintTriggered,
      required this.reasoning,
      required this.status,
      required this.createdAt,
      this.resolvedAt,
      this.resolvedBy,
      this.conditions});

  factory _$HeldActionImpl.fromJson(Map<String, dynamic> json) =>
      _$$HeldActionImplFromJson(json);

  @override
  final String id;
  @override
  final String sessionId;
  @override
  final String actionType;
  @override
  final String description;
  @override
  final String constraintTriggered;
  @override
  final String reasoning;
  @override
  final HeldActionStatus status;
  @override
  final DateTime createdAt;
  @override
  final DateTime? resolvedAt;
  @override
  final String? resolvedBy;
  @override
  final String? conditions;

  @override
  String toString() {
    return 'HeldAction(id: $id, sessionId: $sessionId, actionType: $actionType, description: $description, constraintTriggered: $constraintTriggered, reasoning: $reasoning, status: $status, createdAt: $createdAt, resolvedAt: $resolvedAt, resolvedBy: $resolvedBy, conditions: $conditions)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HeldActionImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.sessionId, sessionId) ||
                other.sessionId == sessionId) &&
            (identical(other.actionType, actionType) ||
                other.actionType == actionType) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.constraintTriggered, constraintTriggered) ||
                other.constraintTriggered == constraintTriggered) &&
            (identical(other.reasoning, reasoning) ||
                other.reasoning == reasoning) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt) &&
            (identical(other.resolvedAt, resolvedAt) ||
                other.resolvedAt == resolvedAt) &&
            (identical(other.resolvedBy, resolvedBy) ||
                other.resolvedBy == resolvedBy) &&
            (identical(other.conditions, conditions) ||
                other.conditions == conditions));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      sessionId,
      actionType,
      description,
      constraintTriggered,
      reasoning,
      status,
      createdAt,
      resolvedAt,
      resolvedBy,
      conditions);

  /// Create a copy of HeldAction
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$HeldActionImplCopyWith<_$HeldActionImpl> get copyWith =>
      __$$HeldActionImplCopyWithImpl<_$HeldActionImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$HeldActionImplToJson(
      this,
    );
  }
}

abstract class _HeldAction implements HeldAction {
  const factory _HeldAction(
      {required final String id,
      required final String sessionId,
      required final String actionType,
      required final String description,
      required final String constraintTriggered,
      required final String reasoning,
      required final HeldActionStatus status,
      required final DateTime createdAt,
      final DateTime? resolvedAt,
      final String? resolvedBy,
      final String? conditions}) = _$HeldActionImpl;

  factory _HeldAction.fromJson(Map<String, dynamic> json) =
      _$HeldActionImpl.fromJson;

  @override
  String get id;
  @override
  String get sessionId;
  @override
  String get actionType;
  @override
  String get description;
  @override
  String get constraintTriggered;
  @override
  String get reasoning;
  @override
  HeldActionStatus get status;
  @override
  DateTime get createdAt;
  @override
  DateTime? get resolvedAt;
  @override
  String? get resolvedBy;
  @override
  String? get conditions;

  /// Create a copy of HeldAction
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$HeldActionImplCopyWith<_$HeldActionImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
