// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'constraint_set.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

ConstraintSet _$ConstraintSetFromJson(Map<String, dynamic> json) {
  return _ConstraintSet.fromJson(json);
}

/// @nodoc
mixin _$ConstraintSet {
  FinancialConstraint get financial => throw _privateConstructorUsedError;
  OperationalConstraint get operational => throw _privateConstructorUsedError;
  TemporalConstraint get temporal => throw _privateConstructorUsedError;
  DataAccessConstraint get dataAccess => throw _privateConstructorUsedError;
  CommunicationConstraint get communication =>
      throw _privateConstructorUsedError;

  /// Serializes this ConstraintSet to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ConstraintSet
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ConstraintSetCopyWith<ConstraintSet> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ConstraintSetCopyWith<$Res> {
  factory $ConstraintSetCopyWith(
          ConstraintSet value, $Res Function(ConstraintSet) then) =
      _$ConstraintSetCopyWithImpl<$Res, ConstraintSet>;
  @useResult
  $Res call(
      {FinancialConstraint financial,
      OperationalConstraint operational,
      TemporalConstraint temporal,
      DataAccessConstraint dataAccess,
      CommunicationConstraint communication});

  $FinancialConstraintCopyWith<$Res> get financial;
  $OperationalConstraintCopyWith<$Res> get operational;
  $TemporalConstraintCopyWith<$Res> get temporal;
  $DataAccessConstraintCopyWith<$Res> get dataAccess;
  $CommunicationConstraintCopyWith<$Res> get communication;
}

/// @nodoc
class _$ConstraintSetCopyWithImpl<$Res, $Val extends ConstraintSet>
    implements $ConstraintSetCopyWith<$Res> {
  _$ConstraintSetCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ConstraintSet
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? financial = null,
    Object? operational = null,
    Object? temporal = null,
    Object? dataAccess = null,
    Object? communication = null,
  }) {
    return _then(_value.copyWith(
      financial: null == financial
          ? _value.financial
          : financial // ignore: cast_nullable_to_non_nullable
              as FinancialConstraint,
      operational: null == operational
          ? _value.operational
          : operational // ignore: cast_nullable_to_non_nullable
              as OperationalConstraint,
      temporal: null == temporal
          ? _value.temporal
          : temporal // ignore: cast_nullable_to_non_nullable
              as TemporalConstraint,
      dataAccess: null == dataAccess
          ? _value.dataAccess
          : dataAccess // ignore: cast_nullable_to_non_nullable
              as DataAccessConstraint,
      communication: null == communication
          ? _value.communication
          : communication // ignore: cast_nullable_to_non_nullable
              as CommunicationConstraint,
    ) as $Val);
  }

  /// Create a copy of ConstraintSet
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $FinancialConstraintCopyWith<$Res> get financial {
    return $FinancialConstraintCopyWith<$Res>(_value.financial, (value) {
      return _then(_value.copyWith(financial: value) as $Val);
    });
  }

  /// Create a copy of ConstraintSet
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $OperationalConstraintCopyWith<$Res> get operational {
    return $OperationalConstraintCopyWith<$Res>(_value.operational, (value) {
      return _then(_value.copyWith(operational: value) as $Val);
    });
  }

  /// Create a copy of ConstraintSet
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $TemporalConstraintCopyWith<$Res> get temporal {
    return $TemporalConstraintCopyWith<$Res>(_value.temporal, (value) {
      return _then(_value.copyWith(temporal: value) as $Val);
    });
  }

  /// Create a copy of ConstraintSet
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $DataAccessConstraintCopyWith<$Res> get dataAccess {
    return $DataAccessConstraintCopyWith<$Res>(_value.dataAccess, (value) {
      return _then(_value.copyWith(dataAccess: value) as $Val);
    });
  }

  /// Create a copy of ConstraintSet
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $CommunicationConstraintCopyWith<$Res> get communication {
    return $CommunicationConstraintCopyWith<$Res>(_value.communication,
        (value) {
      return _then(_value.copyWith(communication: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$ConstraintSetImplCopyWith<$Res>
    implements $ConstraintSetCopyWith<$Res> {
  factory _$$ConstraintSetImplCopyWith(
          _$ConstraintSetImpl value, $Res Function(_$ConstraintSetImpl) then) =
      __$$ConstraintSetImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {FinancialConstraint financial,
      OperationalConstraint operational,
      TemporalConstraint temporal,
      DataAccessConstraint dataAccess,
      CommunicationConstraint communication});

  @override
  $FinancialConstraintCopyWith<$Res> get financial;
  @override
  $OperationalConstraintCopyWith<$Res> get operational;
  @override
  $TemporalConstraintCopyWith<$Res> get temporal;
  @override
  $DataAccessConstraintCopyWith<$Res> get dataAccess;
  @override
  $CommunicationConstraintCopyWith<$Res> get communication;
}

/// @nodoc
class __$$ConstraintSetImplCopyWithImpl<$Res>
    extends _$ConstraintSetCopyWithImpl<$Res, _$ConstraintSetImpl>
    implements _$$ConstraintSetImplCopyWith<$Res> {
  __$$ConstraintSetImplCopyWithImpl(
      _$ConstraintSetImpl _value, $Res Function(_$ConstraintSetImpl) _then)
      : super(_value, _then);

  /// Create a copy of ConstraintSet
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? financial = null,
    Object? operational = null,
    Object? temporal = null,
    Object? dataAccess = null,
    Object? communication = null,
  }) {
    return _then(_$ConstraintSetImpl(
      financial: null == financial
          ? _value.financial
          : financial // ignore: cast_nullable_to_non_nullable
              as FinancialConstraint,
      operational: null == operational
          ? _value.operational
          : operational // ignore: cast_nullable_to_non_nullable
              as OperationalConstraint,
      temporal: null == temporal
          ? _value.temporal
          : temporal // ignore: cast_nullable_to_non_nullable
              as TemporalConstraint,
      dataAccess: null == dataAccess
          ? _value.dataAccess
          : dataAccess // ignore: cast_nullable_to_non_nullable
              as DataAccessConstraint,
      communication: null == communication
          ? _value.communication
          : communication // ignore: cast_nullable_to_non_nullable
              as CommunicationConstraint,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ConstraintSetImpl implements _ConstraintSet {
  const _$ConstraintSetImpl(
      {required this.financial,
      required this.operational,
      required this.temporal,
      required this.dataAccess,
      required this.communication});

  factory _$ConstraintSetImpl.fromJson(Map<String, dynamic> json) =>
      _$$ConstraintSetImplFromJson(json);

  @override
  final FinancialConstraint financial;
  @override
  final OperationalConstraint operational;
  @override
  final TemporalConstraint temporal;
  @override
  final DataAccessConstraint dataAccess;
  @override
  final CommunicationConstraint communication;

  @override
  String toString() {
    return 'ConstraintSet(financial: $financial, operational: $operational, temporal: $temporal, dataAccess: $dataAccess, communication: $communication)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ConstraintSetImpl &&
            (identical(other.financial, financial) ||
                other.financial == financial) &&
            (identical(other.operational, operational) ||
                other.operational == operational) &&
            (identical(other.temporal, temporal) ||
                other.temporal == temporal) &&
            (identical(other.dataAccess, dataAccess) ||
                other.dataAccess == dataAccess) &&
            (identical(other.communication, communication) ||
                other.communication == communication));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType, financial, operational, temporal, dataAccess, communication);

  /// Create a copy of ConstraintSet
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ConstraintSetImplCopyWith<_$ConstraintSetImpl> get copyWith =>
      __$$ConstraintSetImplCopyWithImpl<_$ConstraintSetImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ConstraintSetImplToJson(
      this,
    );
  }
}

abstract class _ConstraintSet implements ConstraintSet {
  const factory _ConstraintSet(
          {required final FinancialConstraint financial,
          required final OperationalConstraint operational,
          required final TemporalConstraint temporal,
          required final DataAccessConstraint dataAccess,
          required final CommunicationConstraint communication}) =
      _$ConstraintSetImpl;

  factory _ConstraintSet.fromJson(Map<String, dynamic> json) =
      _$ConstraintSetImpl.fromJson;

  @override
  FinancialConstraint get financial;
  @override
  OperationalConstraint get operational;
  @override
  TemporalConstraint get temporal;
  @override
  DataAccessConstraint get dataAccess;
  @override
  CommunicationConstraint get communication;

  /// Create a copy of ConstraintSet
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ConstraintSetImplCopyWith<_$ConstraintSetImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

FinancialConstraint _$FinancialConstraintFromJson(Map<String, dynamic> json) {
  return _FinancialConstraint.fromJson(json);
}

/// @nodoc
mixin _$FinancialConstraint {
  double get maxAmount => throw _privateConstructorUsedError;
  double get currentUsage => throw _privateConstructorUsedError;
  String get currency => throw _privateConstructorUsedError;
  bool get requireApprovalAbove => throw _privateConstructorUsedError;
  double? get approvalThreshold => throw _privateConstructorUsedError;

  /// Serializes this FinancialConstraint to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of FinancialConstraint
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $FinancialConstraintCopyWith<FinancialConstraint> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $FinancialConstraintCopyWith<$Res> {
  factory $FinancialConstraintCopyWith(
          FinancialConstraint value, $Res Function(FinancialConstraint) then) =
      _$FinancialConstraintCopyWithImpl<$Res, FinancialConstraint>;
  @useResult
  $Res call(
      {double maxAmount,
      double currentUsage,
      String currency,
      bool requireApprovalAbove,
      double? approvalThreshold});
}

/// @nodoc
class _$FinancialConstraintCopyWithImpl<$Res, $Val extends FinancialConstraint>
    implements $FinancialConstraintCopyWith<$Res> {
  _$FinancialConstraintCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of FinancialConstraint
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? maxAmount = null,
    Object? currentUsage = null,
    Object? currency = null,
    Object? requireApprovalAbove = null,
    Object? approvalThreshold = freezed,
  }) {
    return _then(_value.copyWith(
      maxAmount: null == maxAmount
          ? _value.maxAmount
          : maxAmount // ignore: cast_nullable_to_non_nullable
              as double,
      currentUsage: null == currentUsage
          ? _value.currentUsage
          : currentUsage // ignore: cast_nullable_to_non_nullable
              as double,
      currency: null == currency
          ? _value.currency
          : currency // ignore: cast_nullable_to_non_nullable
              as String,
      requireApprovalAbove: null == requireApprovalAbove
          ? _value.requireApprovalAbove
          : requireApprovalAbove // ignore: cast_nullable_to_non_nullable
              as bool,
      approvalThreshold: freezed == approvalThreshold
          ? _value.approvalThreshold
          : approvalThreshold // ignore: cast_nullable_to_non_nullable
              as double?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$FinancialConstraintImplCopyWith<$Res>
    implements $FinancialConstraintCopyWith<$Res> {
  factory _$$FinancialConstraintImplCopyWith(_$FinancialConstraintImpl value,
          $Res Function(_$FinancialConstraintImpl) then) =
      __$$FinancialConstraintImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {double maxAmount,
      double currentUsage,
      String currency,
      bool requireApprovalAbove,
      double? approvalThreshold});
}

/// @nodoc
class __$$FinancialConstraintImplCopyWithImpl<$Res>
    extends _$FinancialConstraintCopyWithImpl<$Res, _$FinancialConstraintImpl>
    implements _$$FinancialConstraintImplCopyWith<$Res> {
  __$$FinancialConstraintImplCopyWithImpl(_$FinancialConstraintImpl _value,
      $Res Function(_$FinancialConstraintImpl) _then)
      : super(_value, _then);

  /// Create a copy of FinancialConstraint
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? maxAmount = null,
    Object? currentUsage = null,
    Object? currency = null,
    Object? requireApprovalAbove = null,
    Object? approvalThreshold = freezed,
  }) {
    return _then(_$FinancialConstraintImpl(
      maxAmount: null == maxAmount
          ? _value.maxAmount
          : maxAmount // ignore: cast_nullable_to_non_nullable
              as double,
      currentUsage: null == currentUsage
          ? _value.currentUsage
          : currentUsage // ignore: cast_nullable_to_non_nullable
              as double,
      currency: null == currency
          ? _value.currency
          : currency // ignore: cast_nullable_to_non_nullable
              as String,
      requireApprovalAbove: null == requireApprovalAbove
          ? _value.requireApprovalAbove
          : requireApprovalAbove // ignore: cast_nullable_to_non_nullable
              as bool,
      approvalThreshold: freezed == approvalThreshold
          ? _value.approvalThreshold
          : approvalThreshold // ignore: cast_nullable_to_non_nullable
              as double?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$FinancialConstraintImpl implements _FinancialConstraint {
  const _$FinancialConstraintImpl(
      {required this.maxAmount,
      required this.currentUsage,
      required this.currency,
      this.requireApprovalAbove = false,
      this.approvalThreshold});

  factory _$FinancialConstraintImpl.fromJson(Map<String, dynamic> json) =>
      _$$FinancialConstraintImplFromJson(json);

  @override
  final double maxAmount;
  @override
  final double currentUsage;
  @override
  final String currency;
  @override
  @JsonKey()
  final bool requireApprovalAbove;
  @override
  final double? approvalThreshold;

  @override
  String toString() {
    return 'FinancialConstraint(maxAmount: $maxAmount, currentUsage: $currentUsage, currency: $currency, requireApprovalAbove: $requireApprovalAbove, approvalThreshold: $approvalThreshold)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$FinancialConstraintImpl &&
            (identical(other.maxAmount, maxAmount) ||
                other.maxAmount == maxAmount) &&
            (identical(other.currentUsage, currentUsage) ||
                other.currentUsage == currentUsage) &&
            (identical(other.currency, currency) ||
                other.currency == currency) &&
            (identical(other.requireApprovalAbove, requireApprovalAbove) ||
                other.requireApprovalAbove == requireApprovalAbove) &&
            (identical(other.approvalThreshold, approvalThreshold) ||
                other.approvalThreshold == approvalThreshold));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, maxAmount, currentUsage,
      currency, requireApprovalAbove, approvalThreshold);

  /// Create a copy of FinancialConstraint
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$FinancialConstraintImplCopyWith<_$FinancialConstraintImpl> get copyWith =>
      __$$FinancialConstraintImplCopyWithImpl<_$FinancialConstraintImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$FinancialConstraintImplToJson(
      this,
    );
  }
}

abstract class _FinancialConstraint implements FinancialConstraint {
  const factory _FinancialConstraint(
      {required final double maxAmount,
      required final double currentUsage,
      required final String currency,
      final bool requireApprovalAbove,
      final double? approvalThreshold}) = _$FinancialConstraintImpl;

  factory _FinancialConstraint.fromJson(Map<String, dynamic> json) =
      _$FinancialConstraintImpl.fromJson;

  @override
  double get maxAmount;
  @override
  double get currentUsage;
  @override
  String get currency;
  @override
  bool get requireApprovalAbove;
  @override
  double? get approvalThreshold;

  /// Create a copy of FinancialConstraint
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$FinancialConstraintImplCopyWith<_$FinancialConstraintImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

OperationalConstraint _$OperationalConstraintFromJson(
    Map<String, dynamic> json) {
  return _OperationalConstraint.fromJson(json);
}

/// @nodoc
mixin _$OperationalConstraint {
  List<String> get allowedActions => throw _privateConstructorUsedError;
  List<String> get blockedActions => throw _privateConstructorUsedError;
  bool get requireApprovalForDestructive => throw _privateConstructorUsedError;

  /// Serializes this OperationalConstraint to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of OperationalConstraint
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $OperationalConstraintCopyWith<OperationalConstraint> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $OperationalConstraintCopyWith<$Res> {
  factory $OperationalConstraintCopyWith(OperationalConstraint value,
          $Res Function(OperationalConstraint) then) =
      _$OperationalConstraintCopyWithImpl<$Res, OperationalConstraint>;
  @useResult
  $Res call(
      {List<String> allowedActions,
      List<String> blockedActions,
      bool requireApprovalForDestructive});
}

/// @nodoc
class _$OperationalConstraintCopyWithImpl<$Res,
        $Val extends OperationalConstraint>
    implements $OperationalConstraintCopyWith<$Res> {
  _$OperationalConstraintCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of OperationalConstraint
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? allowedActions = null,
    Object? blockedActions = null,
    Object? requireApprovalForDestructive = null,
  }) {
    return _then(_value.copyWith(
      allowedActions: null == allowedActions
          ? _value.allowedActions
          : allowedActions // ignore: cast_nullable_to_non_nullable
              as List<String>,
      blockedActions: null == blockedActions
          ? _value.blockedActions
          : blockedActions // ignore: cast_nullable_to_non_nullable
              as List<String>,
      requireApprovalForDestructive: null == requireApprovalForDestructive
          ? _value.requireApprovalForDestructive
          : requireApprovalForDestructive // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$OperationalConstraintImplCopyWith<$Res>
    implements $OperationalConstraintCopyWith<$Res> {
  factory _$$OperationalConstraintImplCopyWith(
          _$OperationalConstraintImpl value,
          $Res Function(_$OperationalConstraintImpl) then) =
      __$$OperationalConstraintImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {List<String> allowedActions,
      List<String> blockedActions,
      bool requireApprovalForDestructive});
}

/// @nodoc
class __$$OperationalConstraintImplCopyWithImpl<$Res>
    extends _$OperationalConstraintCopyWithImpl<$Res,
        _$OperationalConstraintImpl>
    implements _$$OperationalConstraintImplCopyWith<$Res> {
  __$$OperationalConstraintImplCopyWithImpl(_$OperationalConstraintImpl _value,
      $Res Function(_$OperationalConstraintImpl) _then)
      : super(_value, _then);

  /// Create a copy of OperationalConstraint
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? allowedActions = null,
    Object? blockedActions = null,
    Object? requireApprovalForDestructive = null,
  }) {
    return _then(_$OperationalConstraintImpl(
      allowedActions: null == allowedActions
          ? _value._allowedActions
          : allowedActions // ignore: cast_nullable_to_non_nullable
              as List<String>,
      blockedActions: null == blockedActions
          ? _value._blockedActions
          : blockedActions // ignore: cast_nullable_to_non_nullable
              as List<String>,
      requireApprovalForDestructive: null == requireApprovalForDestructive
          ? _value.requireApprovalForDestructive
          : requireApprovalForDestructive // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$OperationalConstraintImpl implements _OperationalConstraint {
  const _$OperationalConstraintImpl(
      {required final List<String> allowedActions,
      required final List<String> blockedActions,
      this.requireApprovalForDestructive = false})
      : _allowedActions = allowedActions,
        _blockedActions = blockedActions;

  factory _$OperationalConstraintImpl.fromJson(Map<String, dynamic> json) =>
      _$$OperationalConstraintImplFromJson(json);

  final List<String> _allowedActions;
  @override
  List<String> get allowedActions {
    if (_allowedActions is EqualUnmodifiableListView) return _allowedActions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_allowedActions);
  }

  final List<String> _blockedActions;
  @override
  List<String> get blockedActions {
    if (_blockedActions is EqualUnmodifiableListView) return _blockedActions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_blockedActions);
  }

  @override
  @JsonKey()
  final bool requireApprovalForDestructive;

  @override
  String toString() {
    return 'OperationalConstraint(allowedActions: $allowedActions, blockedActions: $blockedActions, requireApprovalForDestructive: $requireApprovalForDestructive)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$OperationalConstraintImpl &&
            const DeepCollectionEquality()
                .equals(other._allowedActions, _allowedActions) &&
            const DeepCollectionEquality()
                .equals(other._blockedActions, _blockedActions) &&
            (identical(other.requireApprovalForDestructive,
                    requireApprovalForDestructive) ||
                other.requireApprovalForDestructive ==
                    requireApprovalForDestructive));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_allowedActions),
      const DeepCollectionEquality().hash(_blockedActions),
      requireApprovalForDestructive);

  /// Create a copy of OperationalConstraint
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$OperationalConstraintImplCopyWith<_$OperationalConstraintImpl>
      get copyWith => __$$OperationalConstraintImplCopyWithImpl<
          _$OperationalConstraintImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$OperationalConstraintImplToJson(
      this,
    );
  }
}

abstract class _OperationalConstraint implements OperationalConstraint {
  const factory _OperationalConstraint(
      {required final List<String> allowedActions,
      required final List<String> blockedActions,
      final bool requireApprovalForDestructive}) = _$OperationalConstraintImpl;

  factory _OperationalConstraint.fromJson(Map<String, dynamic> json) =
      _$OperationalConstraintImpl.fromJson;

  @override
  List<String> get allowedActions;
  @override
  List<String> get blockedActions;
  @override
  bool get requireApprovalForDestructive;

  /// Create a copy of OperationalConstraint
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$OperationalConstraintImplCopyWith<_$OperationalConstraintImpl>
      get copyWith => throw _privateConstructorUsedError;
}

TemporalConstraint _$TemporalConstraintFromJson(Map<String, dynamic> json) {
  return _TemporalConstraint.fromJson(json);
}

/// @nodoc
mixin _$TemporalConstraint {
  DateTime? get validFrom => throw _privateConstructorUsedError;
  DateTime? get validUntil => throw _privateConstructorUsedError;
  int? get maxDurationMinutes => throw _privateConstructorUsedError;
  List<String>? get allowedTimeWindows => throw _privateConstructorUsedError;

  /// Serializes this TemporalConstraint to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of TemporalConstraint
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $TemporalConstraintCopyWith<TemporalConstraint> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $TemporalConstraintCopyWith<$Res> {
  factory $TemporalConstraintCopyWith(
          TemporalConstraint value, $Res Function(TemporalConstraint) then) =
      _$TemporalConstraintCopyWithImpl<$Res, TemporalConstraint>;
  @useResult
  $Res call(
      {DateTime? validFrom,
      DateTime? validUntil,
      int? maxDurationMinutes,
      List<String>? allowedTimeWindows});
}

/// @nodoc
class _$TemporalConstraintCopyWithImpl<$Res, $Val extends TemporalConstraint>
    implements $TemporalConstraintCopyWith<$Res> {
  _$TemporalConstraintCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of TemporalConstraint
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? validFrom = freezed,
    Object? validUntil = freezed,
    Object? maxDurationMinutes = freezed,
    Object? allowedTimeWindows = freezed,
  }) {
    return _then(_value.copyWith(
      validFrom: freezed == validFrom
          ? _value.validFrom
          : validFrom // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      validUntil: freezed == validUntil
          ? _value.validUntil
          : validUntil // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      maxDurationMinutes: freezed == maxDurationMinutes
          ? _value.maxDurationMinutes
          : maxDurationMinutes // ignore: cast_nullable_to_non_nullable
              as int?,
      allowedTimeWindows: freezed == allowedTimeWindows
          ? _value.allowedTimeWindows
          : allowedTimeWindows // ignore: cast_nullable_to_non_nullable
              as List<String>?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$TemporalConstraintImplCopyWith<$Res>
    implements $TemporalConstraintCopyWith<$Res> {
  factory _$$TemporalConstraintImplCopyWith(_$TemporalConstraintImpl value,
          $Res Function(_$TemporalConstraintImpl) then) =
      __$$TemporalConstraintImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {DateTime? validFrom,
      DateTime? validUntil,
      int? maxDurationMinutes,
      List<String>? allowedTimeWindows});
}

/// @nodoc
class __$$TemporalConstraintImplCopyWithImpl<$Res>
    extends _$TemporalConstraintCopyWithImpl<$Res, _$TemporalConstraintImpl>
    implements _$$TemporalConstraintImplCopyWith<$Res> {
  __$$TemporalConstraintImplCopyWithImpl(_$TemporalConstraintImpl _value,
      $Res Function(_$TemporalConstraintImpl) _then)
      : super(_value, _then);

  /// Create a copy of TemporalConstraint
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? validFrom = freezed,
    Object? validUntil = freezed,
    Object? maxDurationMinutes = freezed,
    Object? allowedTimeWindows = freezed,
  }) {
    return _then(_$TemporalConstraintImpl(
      validFrom: freezed == validFrom
          ? _value.validFrom
          : validFrom // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      validUntil: freezed == validUntil
          ? _value.validUntil
          : validUntil // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      maxDurationMinutes: freezed == maxDurationMinutes
          ? _value.maxDurationMinutes
          : maxDurationMinutes // ignore: cast_nullable_to_non_nullable
              as int?,
      allowedTimeWindows: freezed == allowedTimeWindows
          ? _value._allowedTimeWindows
          : allowedTimeWindows // ignore: cast_nullable_to_non_nullable
              as List<String>?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$TemporalConstraintImpl implements _TemporalConstraint {
  const _$TemporalConstraintImpl(
      {this.validFrom,
      this.validUntil,
      this.maxDurationMinutes,
      final List<String>? allowedTimeWindows})
      : _allowedTimeWindows = allowedTimeWindows;

  factory _$TemporalConstraintImpl.fromJson(Map<String, dynamic> json) =>
      _$$TemporalConstraintImplFromJson(json);

  @override
  final DateTime? validFrom;
  @override
  final DateTime? validUntil;
  @override
  final int? maxDurationMinutes;
  final List<String>? _allowedTimeWindows;
  @override
  List<String>? get allowedTimeWindows {
    final value = _allowedTimeWindows;
    if (value == null) return null;
    if (_allowedTimeWindows is EqualUnmodifiableListView)
      return _allowedTimeWindows;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  @override
  String toString() {
    return 'TemporalConstraint(validFrom: $validFrom, validUntil: $validUntil, maxDurationMinutes: $maxDurationMinutes, allowedTimeWindows: $allowedTimeWindows)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$TemporalConstraintImpl &&
            (identical(other.validFrom, validFrom) ||
                other.validFrom == validFrom) &&
            (identical(other.validUntil, validUntil) ||
                other.validUntil == validUntil) &&
            (identical(other.maxDurationMinutes, maxDurationMinutes) ||
                other.maxDurationMinutes == maxDurationMinutes) &&
            const DeepCollectionEquality()
                .equals(other._allowedTimeWindows, _allowedTimeWindows));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      validFrom,
      validUntil,
      maxDurationMinutes,
      const DeepCollectionEquality().hash(_allowedTimeWindows));

  /// Create a copy of TemporalConstraint
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$TemporalConstraintImplCopyWith<_$TemporalConstraintImpl> get copyWith =>
      __$$TemporalConstraintImplCopyWithImpl<_$TemporalConstraintImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$TemporalConstraintImplToJson(
      this,
    );
  }
}

abstract class _TemporalConstraint implements TemporalConstraint {
  const factory _TemporalConstraint(
      {final DateTime? validFrom,
      final DateTime? validUntil,
      final int? maxDurationMinutes,
      final List<String>? allowedTimeWindows}) = _$TemporalConstraintImpl;

  factory _TemporalConstraint.fromJson(Map<String, dynamic> json) =
      _$TemporalConstraintImpl.fromJson;

  @override
  DateTime? get validFrom;
  @override
  DateTime? get validUntil;
  @override
  int? get maxDurationMinutes;
  @override
  List<String>? get allowedTimeWindows;

  /// Create a copy of TemporalConstraint
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$TemporalConstraintImplCopyWith<_$TemporalConstraintImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

DataAccessConstraint _$DataAccessConstraintFromJson(Map<String, dynamic> json) {
  return _DataAccessConstraint.fromJson(json);
}

/// @nodoc
mixin _$DataAccessConstraint {
  List<String> get allowedResources => throw _privateConstructorUsedError;
  List<String> get blockedResources => throw _privateConstructorUsedError;
  String get defaultAccess => throw _privateConstructorUsedError;
  bool get requireApprovalForWrite => throw _privateConstructorUsedError;

  /// Serializes this DataAccessConstraint to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of DataAccessConstraint
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $DataAccessConstraintCopyWith<DataAccessConstraint> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DataAccessConstraintCopyWith<$Res> {
  factory $DataAccessConstraintCopyWith(DataAccessConstraint value,
          $Res Function(DataAccessConstraint) then) =
      _$DataAccessConstraintCopyWithImpl<$Res, DataAccessConstraint>;
  @useResult
  $Res call(
      {List<String> allowedResources,
      List<String> blockedResources,
      String defaultAccess,
      bool requireApprovalForWrite});
}

/// @nodoc
class _$DataAccessConstraintCopyWithImpl<$Res,
        $Val extends DataAccessConstraint>
    implements $DataAccessConstraintCopyWith<$Res> {
  _$DataAccessConstraintCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of DataAccessConstraint
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? allowedResources = null,
    Object? blockedResources = null,
    Object? defaultAccess = null,
    Object? requireApprovalForWrite = null,
  }) {
    return _then(_value.copyWith(
      allowedResources: null == allowedResources
          ? _value.allowedResources
          : allowedResources // ignore: cast_nullable_to_non_nullable
              as List<String>,
      blockedResources: null == blockedResources
          ? _value.blockedResources
          : blockedResources // ignore: cast_nullable_to_non_nullable
              as List<String>,
      defaultAccess: null == defaultAccess
          ? _value.defaultAccess
          : defaultAccess // ignore: cast_nullable_to_non_nullable
              as String,
      requireApprovalForWrite: null == requireApprovalForWrite
          ? _value.requireApprovalForWrite
          : requireApprovalForWrite // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$DataAccessConstraintImplCopyWith<$Res>
    implements $DataAccessConstraintCopyWith<$Res> {
  factory _$$DataAccessConstraintImplCopyWith(_$DataAccessConstraintImpl value,
          $Res Function(_$DataAccessConstraintImpl) then) =
      __$$DataAccessConstraintImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {List<String> allowedResources,
      List<String> blockedResources,
      String defaultAccess,
      bool requireApprovalForWrite});
}

/// @nodoc
class __$$DataAccessConstraintImplCopyWithImpl<$Res>
    extends _$DataAccessConstraintCopyWithImpl<$Res, _$DataAccessConstraintImpl>
    implements _$$DataAccessConstraintImplCopyWith<$Res> {
  __$$DataAccessConstraintImplCopyWithImpl(_$DataAccessConstraintImpl _value,
      $Res Function(_$DataAccessConstraintImpl) _then)
      : super(_value, _then);

  /// Create a copy of DataAccessConstraint
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? allowedResources = null,
    Object? blockedResources = null,
    Object? defaultAccess = null,
    Object? requireApprovalForWrite = null,
  }) {
    return _then(_$DataAccessConstraintImpl(
      allowedResources: null == allowedResources
          ? _value._allowedResources
          : allowedResources // ignore: cast_nullable_to_non_nullable
              as List<String>,
      blockedResources: null == blockedResources
          ? _value._blockedResources
          : blockedResources // ignore: cast_nullable_to_non_nullable
              as List<String>,
      defaultAccess: null == defaultAccess
          ? _value.defaultAccess
          : defaultAccess // ignore: cast_nullable_to_non_nullable
              as String,
      requireApprovalForWrite: null == requireApprovalForWrite
          ? _value.requireApprovalForWrite
          : requireApprovalForWrite // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$DataAccessConstraintImpl implements _DataAccessConstraint {
  const _$DataAccessConstraintImpl(
      {required final List<String> allowedResources,
      required final List<String> blockedResources,
      this.defaultAccess = 'read',
      this.requireApprovalForWrite = false})
      : _allowedResources = allowedResources,
        _blockedResources = blockedResources;

  factory _$DataAccessConstraintImpl.fromJson(Map<String, dynamic> json) =>
      _$$DataAccessConstraintImplFromJson(json);

  final List<String> _allowedResources;
  @override
  List<String> get allowedResources {
    if (_allowedResources is EqualUnmodifiableListView)
      return _allowedResources;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_allowedResources);
  }

  final List<String> _blockedResources;
  @override
  List<String> get blockedResources {
    if (_blockedResources is EqualUnmodifiableListView)
      return _blockedResources;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_blockedResources);
  }

  @override
  @JsonKey()
  final String defaultAccess;
  @override
  @JsonKey()
  final bool requireApprovalForWrite;

  @override
  String toString() {
    return 'DataAccessConstraint(allowedResources: $allowedResources, blockedResources: $blockedResources, defaultAccess: $defaultAccess, requireApprovalForWrite: $requireApprovalForWrite)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DataAccessConstraintImpl &&
            const DeepCollectionEquality()
                .equals(other._allowedResources, _allowedResources) &&
            const DeepCollectionEquality()
                .equals(other._blockedResources, _blockedResources) &&
            (identical(other.defaultAccess, defaultAccess) ||
                other.defaultAccess == defaultAccess) &&
            (identical(
                    other.requireApprovalForWrite, requireApprovalForWrite) ||
                other.requireApprovalForWrite == requireApprovalForWrite));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_allowedResources),
      const DeepCollectionEquality().hash(_blockedResources),
      defaultAccess,
      requireApprovalForWrite);

  /// Create a copy of DataAccessConstraint
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$DataAccessConstraintImplCopyWith<_$DataAccessConstraintImpl>
      get copyWith =>
          __$$DataAccessConstraintImplCopyWithImpl<_$DataAccessConstraintImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$DataAccessConstraintImplToJson(
      this,
    );
  }
}

abstract class _DataAccessConstraint implements DataAccessConstraint {
  const factory _DataAccessConstraint(
      {required final List<String> allowedResources,
      required final List<String> blockedResources,
      final String defaultAccess,
      final bool requireApprovalForWrite}) = _$DataAccessConstraintImpl;

  factory _DataAccessConstraint.fromJson(Map<String, dynamic> json) =
      _$DataAccessConstraintImpl.fromJson;

  @override
  List<String> get allowedResources;
  @override
  List<String> get blockedResources;
  @override
  String get defaultAccess;
  @override
  bool get requireApprovalForWrite;

  /// Create a copy of DataAccessConstraint
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$DataAccessConstraintImplCopyWith<_$DataAccessConstraintImpl>
      get copyWith => throw _privateConstructorUsedError;
}

CommunicationConstraint _$CommunicationConstraintFromJson(
    Map<String, dynamic> json) {
  return _CommunicationConstraint.fromJson(json);
}

/// @nodoc
mixin _$CommunicationConstraint {
  List<String> get allowedChannels => throw _privateConstructorUsedError;
  List<String> get blockedChannels => throw _privateConstructorUsedError;
  bool get requireApprovalForExternal => throw _privateConstructorUsedError;

  /// Serializes this CommunicationConstraint to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of CommunicationConstraint
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $CommunicationConstraintCopyWith<CommunicationConstraint> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CommunicationConstraintCopyWith<$Res> {
  factory $CommunicationConstraintCopyWith(CommunicationConstraint value,
          $Res Function(CommunicationConstraint) then) =
      _$CommunicationConstraintCopyWithImpl<$Res, CommunicationConstraint>;
  @useResult
  $Res call(
      {List<String> allowedChannels,
      List<String> blockedChannels,
      bool requireApprovalForExternal});
}

/// @nodoc
class _$CommunicationConstraintCopyWithImpl<$Res,
        $Val extends CommunicationConstraint>
    implements $CommunicationConstraintCopyWith<$Res> {
  _$CommunicationConstraintCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of CommunicationConstraint
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? allowedChannels = null,
    Object? blockedChannels = null,
    Object? requireApprovalForExternal = null,
  }) {
    return _then(_value.copyWith(
      allowedChannels: null == allowedChannels
          ? _value.allowedChannels
          : allowedChannels // ignore: cast_nullable_to_non_nullable
              as List<String>,
      blockedChannels: null == blockedChannels
          ? _value.blockedChannels
          : blockedChannels // ignore: cast_nullable_to_non_nullable
              as List<String>,
      requireApprovalForExternal: null == requireApprovalForExternal
          ? _value.requireApprovalForExternal
          : requireApprovalForExternal // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CommunicationConstraintImplCopyWith<$Res>
    implements $CommunicationConstraintCopyWith<$Res> {
  factory _$$CommunicationConstraintImplCopyWith(
          _$CommunicationConstraintImpl value,
          $Res Function(_$CommunicationConstraintImpl) then) =
      __$$CommunicationConstraintImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {List<String> allowedChannels,
      List<String> blockedChannels,
      bool requireApprovalForExternal});
}

/// @nodoc
class __$$CommunicationConstraintImplCopyWithImpl<$Res>
    extends _$CommunicationConstraintCopyWithImpl<$Res,
        _$CommunicationConstraintImpl>
    implements _$$CommunicationConstraintImplCopyWith<$Res> {
  __$$CommunicationConstraintImplCopyWithImpl(
      _$CommunicationConstraintImpl _value,
      $Res Function(_$CommunicationConstraintImpl) _then)
      : super(_value, _then);

  /// Create a copy of CommunicationConstraint
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? allowedChannels = null,
    Object? blockedChannels = null,
    Object? requireApprovalForExternal = null,
  }) {
    return _then(_$CommunicationConstraintImpl(
      allowedChannels: null == allowedChannels
          ? _value._allowedChannels
          : allowedChannels // ignore: cast_nullable_to_non_nullable
              as List<String>,
      blockedChannels: null == blockedChannels
          ? _value._blockedChannels
          : blockedChannels // ignore: cast_nullable_to_non_nullable
              as List<String>,
      requireApprovalForExternal: null == requireApprovalForExternal
          ? _value.requireApprovalForExternal
          : requireApprovalForExternal // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CommunicationConstraintImpl implements _CommunicationConstraint {
  const _$CommunicationConstraintImpl(
      {required final List<String> allowedChannels,
      required final List<String> blockedChannels,
      this.requireApprovalForExternal = false})
      : _allowedChannels = allowedChannels,
        _blockedChannels = blockedChannels;

  factory _$CommunicationConstraintImpl.fromJson(Map<String, dynamic> json) =>
      _$$CommunicationConstraintImplFromJson(json);

  final List<String> _allowedChannels;
  @override
  List<String> get allowedChannels {
    if (_allowedChannels is EqualUnmodifiableListView) return _allowedChannels;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_allowedChannels);
  }

  final List<String> _blockedChannels;
  @override
  List<String> get blockedChannels {
    if (_blockedChannels is EqualUnmodifiableListView) return _blockedChannels;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_blockedChannels);
  }

  @override
  @JsonKey()
  final bool requireApprovalForExternal;

  @override
  String toString() {
    return 'CommunicationConstraint(allowedChannels: $allowedChannels, blockedChannels: $blockedChannels, requireApprovalForExternal: $requireApprovalForExternal)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CommunicationConstraintImpl &&
            const DeepCollectionEquality()
                .equals(other._allowedChannels, _allowedChannels) &&
            const DeepCollectionEquality()
                .equals(other._blockedChannels, _blockedChannels) &&
            (identical(other.requireApprovalForExternal,
                    requireApprovalForExternal) ||
                other.requireApprovalForExternal ==
                    requireApprovalForExternal));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_allowedChannels),
      const DeepCollectionEquality().hash(_blockedChannels),
      requireApprovalForExternal);

  /// Create a copy of CommunicationConstraint
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$CommunicationConstraintImplCopyWith<_$CommunicationConstraintImpl>
      get copyWith => __$$CommunicationConstraintImplCopyWithImpl<
          _$CommunicationConstraintImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CommunicationConstraintImplToJson(
      this,
    );
  }
}

abstract class _CommunicationConstraint implements CommunicationConstraint {
  const factory _CommunicationConstraint(
      {required final List<String> allowedChannels,
      required final List<String> blockedChannels,
      final bool requireApprovalForExternal}) = _$CommunicationConstraintImpl;

  factory _CommunicationConstraint.fromJson(Map<String, dynamic> json) =
      _$CommunicationConstraintImpl.fromJson;

  @override
  List<String> get allowedChannels;
  @override
  List<String> get blockedChannels;
  @override
  bool get requireApprovalForExternal;

  /// Create a copy of CommunicationConstraint
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$CommunicationConstraintImplCopyWith<_$CommunicationConstraintImpl>
      get copyWith => throw _privateConstructorUsedError;
}

ConstraintPreset _$ConstraintPresetFromJson(Map<String, dynamic> json) {
  return _ConstraintPreset.fromJson(json);
}

/// @nodoc
mixin _$ConstraintPreset {
  String get id => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  String get domain => throw _privateConstructorUsedError;
  ConstraintSet get constraints => throw _privateConstructorUsedError;

  /// Serializes this ConstraintPreset to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ConstraintPreset
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ConstraintPresetCopyWith<ConstraintPreset> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ConstraintPresetCopyWith<$Res> {
  factory $ConstraintPresetCopyWith(
          ConstraintPreset value, $Res Function(ConstraintPreset) then) =
      _$ConstraintPresetCopyWithImpl<$Res, ConstraintPreset>;
  @useResult
  $Res call(
      {String id,
      String name,
      String description,
      String domain,
      ConstraintSet constraints});

  $ConstraintSetCopyWith<$Res> get constraints;
}

/// @nodoc
class _$ConstraintPresetCopyWithImpl<$Res, $Val extends ConstraintPreset>
    implements $ConstraintPresetCopyWith<$Res> {
  _$ConstraintPresetCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ConstraintPreset
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? name = null,
    Object? description = null,
    Object? domain = null,
    Object? constraints = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      domain: null == domain
          ? _value.domain
          : domain // ignore: cast_nullable_to_non_nullable
              as String,
      constraints: null == constraints
          ? _value.constraints
          : constraints // ignore: cast_nullable_to_non_nullable
              as ConstraintSet,
    ) as $Val);
  }

  /// Create a copy of ConstraintPreset
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
abstract class _$$ConstraintPresetImplCopyWith<$Res>
    implements $ConstraintPresetCopyWith<$Res> {
  factory _$$ConstraintPresetImplCopyWith(_$ConstraintPresetImpl value,
          $Res Function(_$ConstraintPresetImpl) then) =
      __$$ConstraintPresetImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String name,
      String description,
      String domain,
      ConstraintSet constraints});

  @override
  $ConstraintSetCopyWith<$Res> get constraints;
}

/// @nodoc
class __$$ConstraintPresetImplCopyWithImpl<$Res>
    extends _$ConstraintPresetCopyWithImpl<$Res, _$ConstraintPresetImpl>
    implements _$$ConstraintPresetImplCopyWith<$Res> {
  __$$ConstraintPresetImplCopyWithImpl(_$ConstraintPresetImpl _value,
      $Res Function(_$ConstraintPresetImpl) _then)
      : super(_value, _then);

  /// Create a copy of ConstraintPreset
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? name = null,
    Object? description = null,
    Object? domain = null,
    Object? constraints = null,
  }) {
    return _then(_$ConstraintPresetImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      domain: null == domain
          ? _value.domain
          : domain // ignore: cast_nullable_to_non_nullable
              as String,
      constraints: null == constraints
          ? _value.constraints
          : constraints // ignore: cast_nullable_to_non_nullable
              as ConstraintSet,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ConstraintPresetImpl implements _ConstraintPreset {
  const _$ConstraintPresetImpl(
      {required this.id,
      required this.name,
      required this.description,
      required this.domain,
      required this.constraints});

  factory _$ConstraintPresetImpl.fromJson(Map<String, dynamic> json) =>
      _$$ConstraintPresetImplFromJson(json);

  @override
  final String id;
  @override
  final String name;
  @override
  final String description;
  @override
  final String domain;
  @override
  final ConstraintSet constraints;

  @override
  String toString() {
    return 'ConstraintPreset(id: $id, name: $name, description: $description, domain: $domain, constraints: $constraints)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ConstraintPresetImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.domain, domain) || other.domain == domain) &&
            (identical(other.constraints, constraints) ||
                other.constraints == constraints));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, id, name, description, domain, constraints);

  /// Create a copy of ConstraintPreset
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ConstraintPresetImplCopyWith<_$ConstraintPresetImpl> get copyWith =>
      __$$ConstraintPresetImplCopyWithImpl<_$ConstraintPresetImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ConstraintPresetImplToJson(
      this,
    );
  }
}

abstract class _ConstraintPreset implements ConstraintPreset {
  const factory _ConstraintPreset(
      {required final String id,
      required final String name,
      required final String description,
      required final String domain,
      required final ConstraintSet constraints}) = _$ConstraintPresetImpl;

  factory _ConstraintPreset.fromJson(Map<String, dynamic> json) =
      _$ConstraintPresetImpl.fromJson;

  @override
  String get id;
  @override
  String get name;
  @override
  String get description;
  @override
  String get domain;
  @override
  ConstraintSet get constraints;

  /// Create a copy of ConstraintPreset
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ConstraintPresetImplCopyWith<_$ConstraintPresetImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
