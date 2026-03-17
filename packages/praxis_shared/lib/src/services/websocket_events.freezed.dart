// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'websocket_events.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

WebSocketEvent _$WebSocketEventFromJson(Map<String, dynamic> json) {
  switch (json['runtimeType']) {
    case 'sessionCreated':
      return SessionCreatedEvent.fromJson(json);
    case 'sessionUpdated':
      return SessionUpdatedEvent.fromJson(json);
    case 'sessionEnded':
      return SessionEndedEvent.fromJson(json);
    case 'constraintUpdated':
      return ConstraintUpdatedEvent.fromJson(json);
    case 'constraintViolation':
      return ConstraintViolationEvent.fromJson(json);
    case 'actionHeld':
      return ActionHeldEvent.fromJson(json);
    case 'actionResolved':
      return ActionResolvedEvent.fromJson(json);
    case 'trustEntryAdded':
      return TrustEntryAddedEvent.fromJson(json);
    case 'heartbeat':
      return HeartbeatEvent.fromJson(json);
    case 'error':
      return ErrorEvent.fromJson(json);

    default:
      throw CheckedFromJsonException(json, 'runtimeType', 'WebSocketEvent',
          'Invalid union type "${json['runtimeType']}"!');
  }
}

/// @nodoc
mixin _$WebSocketEvent {
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(Session session) sessionCreated,
    required TResult Function(Session session) sessionUpdated,
    required TResult Function(String sessionId) sessionEnded,
    required TResult Function(String sessionId, ConstraintSet constraints)
        constraintUpdated,
    required TResult Function(
            String sessionId, String dimension, String description)
        constraintViolation,
    required TResult Function(HeldAction action) actionHeld,
    required TResult Function(HeldAction action) actionResolved,
    required TResult Function(String sessionId, TrustEntry entry)
        trustEntryAdded,
    required TResult Function() heartbeat,
    required TResult Function(String message) error,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(Session session)? sessionCreated,
    TResult? Function(Session session)? sessionUpdated,
    TResult? Function(String sessionId)? sessionEnded,
    TResult? Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult? Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult? Function(HeldAction action)? actionHeld,
    TResult? Function(HeldAction action)? actionResolved,
    TResult? Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult? Function()? heartbeat,
    TResult? Function(String message)? error,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(Session session)? sessionCreated,
    TResult Function(Session session)? sessionUpdated,
    TResult Function(String sessionId)? sessionEnded,
    TResult Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult Function(HeldAction action)? actionHeld,
    TResult Function(HeldAction action)? actionResolved,
    TResult Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult Function()? heartbeat,
    TResult Function(String message)? error,
    required TResult orElse(),
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(SessionCreatedEvent value) sessionCreated,
    required TResult Function(SessionUpdatedEvent value) sessionUpdated,
    required TResult Function(SessionEndedEvent value) sessionEnded,
    required TResult Function(ConstraintUpdatedEvent value) constraintUpdated,
    required TResult Function(ConstraintViolationEvent value)
        constraintViolation,
    required TResult Function(ActionHeldEvent value) actionHeld,
    required TResult Function(ActionResolvedEvent value) actionResolved,
    required TResult Function(TrustEntryAddedEvent value) trustEntryAdded,
    required TResult Function(HeartbeatEvent value) heartbeat,
    required TResult Function(ErrorEvent value) error,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(SessionCreatedEvent value)? sessionCreated,
    TResult? Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult? Function(SessionEndedEvent value)? sessionEnded,
    TResult? Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult? Function(ConstraintViolationEvent value)? constraintViolation,
    TResult? Function(ActionHeldEvent value)? actionHeld,
    TResult? Function(ActionResolvedEvent value)? actionResolved,
    TResult? Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult? Function(HeartbeatEvent value)? heartbeat,
    TResult? Function(ErrorEvent value)? error,
  }) =>
      throw _privateConstructorUsedError;
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(SessionCreatedEvent value)? sessionCreated,
    TResult Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult Function(SessionEndedEvent value)? sessionEnded,
    TResult Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult Function(ConstraintViolationEvent value)? constraintViolation,
    TResult Function(ActionHeldEvent value)? actionHeld,
    TResult Function(ActionResolvedEvent value)? actionResolved,
    TResult Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult Function(HeartbeatEvent value)? heartbeat,
    TResult Function(ErrorEvent value)? error,
    required TResult orElse(),
  }) =>
      throw _privateConstructorUsedError;

  /// Serializes this WebSocketEvent to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $WebSocketEventCopyWith<$Res> {
  factory $WebSocketEventCopyWith(
          WebSocketEvent value, $Res Function(WebSocketEvent) then) =
      _$WebSocketEventCopyWithImpl<$Res, WebSocketEvent>;
}

/// @nodoc
class _$WebSocketEventCopyWithImpl<$Res, $Val extends WebSocketEvent>
    implements $WebSocketEventCopyWith<$Res> {
  _$WebSocketEventCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
}

/// @nodoc
abstract class _$$SessionCreatedEventImplCopyWith<$Res> {
  factory _$$SessionCreatedEventImplCopyWith(_$SessionCreatedEventImpl value,
          $Res Function(_$SessionCreatedEventImpl) then) =
      __$$SessionCreatedEventImplCopyWithImpl<$Res>;
  @useResult
  $Res call({Session session});

  $SessionCopyWith<$Res> get session;
}

/// @nodoc
class __$$SessionCreatedEventImplCopyWithImpl<$Res>
    extends _$WebSocketEventCopyWithImpl<$Res, _$SessionCreatedEventImpl>
    implements _$$SessionCreatedEventImplCopyWith<$Res> {
  __$$SessionCreatedEventImplCopyWithImpl(_$SessionCreatedEventImpl _value,
      $Res Function(_$SessionCreatedEventImpl) _then)
      : super(_value, _then);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? session = null,
  }) {
    return _then(_$SessionCreatedEventImpl(
      null == session
          ? _value.session
          : session // ignore: cast_nullable_to_non_nullable
              as Session,
    ));
  }

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SessionCopyWith<$Res> get session {
    return $SessionCopyWith<$Res>(_value.session, (value) {
      return _then(_value.copyWith(session: value));
    });
  }
}

/// @nodoc
@JsonSerializable()
class _$SessionCreatedEventImpl implements SessionCreatedEvent {
  const _$SessionCreatedEventImpl(this.session, {final String? $type})
      : $type = $type ?? 'sessionCreated';

  factory _$SessionCreatedEventImpl.fromJson(Map<String, dynamic> json) =>
      _$$SessionCreatedEventImplFromJson(json);

  @override
  final Session session;

  @JsonKey(name: 'runtimeType')
  final String $type;

  @override
  String toString() {
    return 'WebSocketEvent.sessionCreated(session: $session)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SessionCreatedEventImpl &&
            (identical(other.session, session) || other.session == session));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, session);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$SessionCreatedEventImplCopyWith<_$SessionCreatedEventImpl> get copyWith =>
      __$$SessionCreatedEventImplCopyWithImpl<_$SessionCreatedEventImpl>(
          this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(Session session) sessionCreated,
    required TResult Function(Session session) sessionUpdated,
    required TResult Function(String sessionId) sessionEnded,
    required TResult Function(String sessionId, ConstraintSet constraints)
        constraintUpdated,
    required TResult Function(
            String sessionId, String dimension, String description)
        constraintViolation,
    required TResult Function(HeldAction action) actionHeld,
    required TResult Function(HeldAction action) actionResolved,
    required TResult Function(String sessionId, TrustEntry entry)
        trustEntryAdded,
    required TResult Function() heartbeat,
    required TResult Function(String message) error,
  }) {
    return sessionCreated(session);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(Session session)? sessionCreated,
    TResult? Function(Session session)? sessionUpdated,
    TResult? Function(String sessionId)? sessionEnded,
    TResult? Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult? Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult? Function(HeldAction action)? actionHeld,
    TResult? Function(HeldAction action)? actionResolved,
    TResult? Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult? Function()? heartbeat,
    TResult? Function(String message)? error,
  }) {
    return sessionCreated?.call(session);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(Session session)? sessionCreated,
    TResult Function(Session session)? sessionUpdated,
    TResult Function(String sessionId)? sessionEnded,
    TResult Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult Function(HeldAction action)? actionHeld,
    TResult Function(HeldAction action)? actionResolved,
    TResult Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult Function()? heartbeat,
    TResult Function(String message)? error,
    required TResult orElse(),
  }) {
    if (sessionCreated != null) {
      return sessionCreated(session);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(SessionCreatedEvent value) sessionCreated,
    required TResult Function(SessionUpdatedEvent value) sessionUpdated,
    required TResult Function(SessionEndedEvent value) sessionEnded,
    required TResult Function(ConstraintUpdatedEvent value) constraintUpdated,
    required TResult Function(ConstraintViolationEvent value)
        constraintViolation,
    required TResult Function(ActionHeldEvent value) actionHeld,
    required TResult Function(ActionResolvedEvent value) actionResolved,
    required TResult Function(TrustEntryAddedEvent value) trustEntryAdded,
    required TResult Function(HeartbeatEvent value) heartbeat,
    required TResult Function(ErrorEvent value) error,
  }) {
    return sessionCreated(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(SessionCreatedEvent value)? sessionCreated,
    TResult? Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult? Function(SessionEndedEvent value)? sessionEnded,
    TResult? Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult? Function(ConstraintViolationEvent value)? constraintViolation,
    TResult? Function(ActionHeldEvent value)? actionHeld,
    TResult? Function(ActionResolvedEvent value)? actionResolved,
    TResult? Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult? Function(HeartbeatEvent value)? heartbeat,
    TResult? Function(ErrorEvent value)? error,
  }) {
    return sessionCreated?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(SessionCreatedEvent value)? sessionCreated,
    TResult Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult Function(SessionEndedEvent value)? sessionEnded,
    TResult Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult Function(ConstraintViolationEvent value)? constraintViolation,
    TResult Function(ActionHeldEvent value)? actionHeld,
    TResult Function(ActionResolvedEvent value)? actionResolved,
    TResult Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult Function(HeartbeatEvent value)? heartbeat,
    TResult Function(ErrorEvent value)? error,
    required TResult orElse(),
  }) {
    if (sessionCreated != null) {
      return sessionCreated(this);
    }
    return orElse();
  }

  @override
  Map<String, dynamic> toJson() {
    return _$$SessionCreatedEventImplToJson(
      this,
    );
  }
}

abstract class SessionCreatedEvent implements WebSocketEvent {
  const factory SessionCreatedEvent(final Session session) =
      _$SessionCreatedEventImpl;

  factory SessionCreatedEvent.fromJson(Map<String, dynamic> json) =
      _$SessionCreatedEventImpl.fromJson;

  Session get session;

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$SessionCreatedEventImplCopyWith<_$SessionCreatedEventImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$SessionUpdatedEventImplCopyWith<$Res> {
  factory _$$SessionUpdatedEventImplCopyWith(_$SessionUpdatedEventImpl value,
          $Res Function(_$SessionUpdatedEventImpl) then) =
      __$$SessionUpdatedEventImplCopyWithImpl<$Res>;
  @useResult
  $Res call({Session session});

  $SessionCopyWith<$Res> get session;
}

/// @nodoc
class __$$SessionUpdatedEventImplCopyWithImpl<$Res>
    extends _$WebSocketEventCopyWithImpl<$Res, _$SessionUpdatedEventImpl>
    implements _$$SessionUpdatedEventImplCopyWith<$Res> {
  __$$SessionUpdatedEventImplCopyWithImpl(_$SessionUpdatedEventImpl _value,
      $Res Function(_$SessionUpdatedEventImpl) _then)
      : super(_value, _then);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? session = null,
  }) {
    return _then(_$SessionUpdatedEventImpl(
      null == session
          ? _value.session
          : session // ignore: cast_nullable_to_non_nullable
              as Session,
    ));
  }

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $SessionCopyWith<$Res> get session {
    return $SessionCopyWith<$Res>(_value.session, (value) {
      return _then(_value.copyWith(session: value));
    });
  }
}

/// @nodoc
@JsonSerializable()
class _$SessionUpdatedEventImpl implements SessionUpdatedEvent {
  const _$SessionUpdatedEventImpl(this.session, {final String? $type})
      : $type = $type ?? 'sessionUpdated';

  factory _$SessionUpdatedEventImpl.fromJson(Map<String, dynamic> json) =>
      _$$SessionUpdatedEventImplFromJson(json);

  @override
  final Session session;

  @JsonKey(name: 'runtimeType')
  final String $type;

  @override
  String toString() {
    return 'WebSocketEvent.sessionUpdated(session: $session)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SessionUpdatedEventImpl &&
            (identical(other.session, session) || other.session == session));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, session);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$SessionUpdatedEventImplCopyWith<_$SessionUpdatedEventImpl> get copyWith =>
      __$$SessionUpdatedEventImplCopyWithImpl<_$SessionUpdatedEventImpl>(
          this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(Session session) sessionCreated,
    required TResult Function(Session session) sessionUpdated,
    required TResult Function(String sessionId) sessionEnded,
    required TResult Function(String sessionId, ConstraintSet constraints)
        constraintUpdated,
    required TResult Function(
            String sessionId, String dimension, String description)
        constraintViolation,
    required TResult Function(HeldAction action) actionHeld,
    required TResult Function(HeldAction action) actionResolved,
    required TResult Function(String sessionId, TrustEntry entry)
        trustEntryAdded,
    required TResult Function() heartbeat,
    required TResult Function(String message) error,
  }) {
    return sessionUpdated(session);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(Session session)? sessionCreated,
    TResult? Function(Session session)? sessionUpdated,
    TResult? Function(String sessionId)? sessionEnded,
    TResult? Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult? Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult? Function(HeldAction action)? actionHeld,
    TResult? Function(HeldAction action)? actionResolved,
    TResult? Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult? Function()? heartbeat,
    TResult? Function(String message)? error,
  }) {
    return sessionUpdated?.call(session);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(Session session)? sessionCreated,
    TResult Function(Session session)? sessionUpdated,
    TResult Function(String sessionId)? sessionEnded,
    TResult Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult Function(HeldAction action)? actionHeld,
    TResult Function(HeldAction action)? actionResolved,
    TResult Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult Function()? heartbeat,
    TResult Function(String message)? error,
    required TResult orElse(),
  }) {
    if (sessionUpdated != null) {
      return sessionUpdated(session);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(SessionCreatedEvent value) sessionCreated,
    required TResult Function(SessionUpdatedEvent value) sessionUpdated,
    required TResult Function(SessionEndedEvent value) sessionEnded,
    required TResult Function(ConstraintUpdatedEvent value) constraintUpdated,
    required TResult Function(ConstraintViolationEvent value)
        constraintViolation,
    required TResult Function(ActionHeldEvent value) actionHeld,
    required TResult Function(ActionResolvedEvent value) actionResolved,
    required TResult Function(TrustEntryAddedEvent value) trustEntryAdded,
    required TResult Function(HeartbeatEvent value) heartbeat,
    required TResult Function(ErrorEvent value) error,
  }) {
    return sessionUpdated(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(SessionCreatedEvent value)? sessionCreated,
    TResult? Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult? Function(SessionEndedEvent value)? sessionEnded,
    TResult? Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult? Function(ConstraintViolationEvent value)? constraintViolation,
    TResult? Function(ActionHeldEvent value)? actionHeld,
    TResult? Function(ActionResolvedEvent value)? actionResolved,
    TResult? Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult? Function(HeartbeatEvent value)? heartbeat,
    TResult? Function(ErrorEvent value)? error,
  }) {
    return sessionUpdated?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(SessionCreatedEvent value)? sessionCreated,
    TResult Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult Function(SessionEndedEvent value)? sessionEnded,
    TResult Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult Function(ConstraintViolationEvent value)? constraintViolation,
    TResult Function(ActionHeldEvent value)? actionHeld,
    TResult Function(ActionResolvedEvent value)? actionResolved,
    TResult Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult Function(HeartbeatEvent value)? heartbeat,
    TResult Function(ErrorEvent value)? error,
    required TResult orElse(),
  }) {
    if (sessionUpdated != null) {
      return sessionUpdated(this);
    }
    return orElse();
  }

  @override
  Map<String, dynamic> toJson() {
    return _$$SessionUpdatedEventImplToJson(
      this,
    );
  }
}

abstract class SessionUpdatedEvent implements WebSocketEvent {
  const factory SessionUpdatedEvent(final Session session) =
      _$SessionUpdatedEventImpl;

  factory SessionUpdatedEvent.fromJson(Map<String, dynamic> json) =
      _$SessionUpdatedEventImpl.fromJson;

  Session get session;

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$SessionUpdatedEventImplCopyWith<_$SessionUpdatedEventImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$SessionEndedEventImplCopyWith<$Res> {
  factory _$$SessionEndedEventImplCopyWith(_$SessionEndedEventImpl value,
          $Res Function(_$SessionEndedEventImpl) then) =
      __$$SessionEndedEventImplCopyWithImpl<$Res>;
  @useResult
  $Res call({String sessionId});
}

/// @nodoc
class __$$SessionEndedEventImplCopyWithImpl<$Res>
    extends _$WebSocketEventCopyWithImpl<$Res, _$SessionEndedEventImpl>
    implements _$$SessionEndedEventImplCopyWith<$Res> {
  __$$SessionEndedEventImplCopyWithImpl(_$SessionEndedEventImpl _value,
      $Res Function(_$SessionEndedEventImpl) _then)
      : super(_value, _then);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sessionId = null,
  }) {
    return _then(_$SessionEndedEventImpl(
      null == sessionId
          ? _value.sessionId
          : sessionId // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$SessionEndedEventImpl implements SessionEndedEvent {
  const _$SessionEndedEventImpl(this.sessionId, {final String? $type})
      : $type = $type ?? 'sessionEnded';

  factory _$SessionEndedEventImpl.fromJson(Map<String, dynamic> json) =>
      _$$SessionEndedEventImplFromJson(json);

  @override
  final String sessionId;

  @JsonKey(name: 'runtimeType')
  final String $type;

  @override
  String toString() {
    return 'WebSocketEvent.sessionEnded(sessionId: $sessionId)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SessionEndedEventImpl &&
            (identical(other.sessionId, sessionId) ||
                other.sessionId == sessionId));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, sessionId);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$SessionEndedEventImplCopyWith<_$SessionEndedEventImpl> get copyWith =>
      __$$SessionEndedEventImplCopyWithImpl<_$SessionEndedEventImpl>(
          this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(Session session) sessionCreated,
    required TResult Function(Session session) sessionUpdated,
    required TResult Function(String sessionId) sessionEnded,
    required TResult Function(String sessionId, ConstraintSet constraints)
        constraintUpdated,
    required TResult Function(
            String sessionId, String dimension, String description)
        constraintViolation,
    required TResult Function(HeldAction action) actionHeld,
    required TResult Function(HeldAction action) actionResolved,
    required TResult Function(String sessionId, TrustEntry entry)
        trustEntryAdded,
    required TResult Function() heartbeat,
    required TResult Function(String message) error,
  }) {
    return sessionEnded(sessionId);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(Session session)? sessionCreated,
    TResult? Function(Session session)? sessionUpdated,
    TResult? Function(String sessionId)? sessionEnded,
    TResult? Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult? Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult? Function(HeldAction action)? actionHeld,
    TResult? Function(HeldAction action)? actionResolved,
    TResult? Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult? Function()? heartbeat,
    TResult? Function(String message)? error,
  }) {
    return sessionEnded?.call(sessionId);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(Session session)? sessionCreated,
    TResult Function(Session session)? sessionUpdated,
    TResult Function(String sessionId)? sessionEnded,
    TResult Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult Function(HeldAction action)? actionHeld,
    TResult Function(HeldAction action)? actionResolved,
    TResult Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult Function()? heartbeat,
    TResult Function(String message)? error,
    required TResult orElse(),
  }) {
    if (sessionEnded != null) {
      return sessionEnded(sessionId);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(SessionCreatedEvent value) sessionCreated,
    required TResult Function(SessionUpdatedEvent value) sessionUpdated,
    required TResult Function(SessionEndedEvent value) sessionEnded,
    required TResult Function(ConstraintUpdatedEvent value) constraintUpdated,
    required TResult Function(ConstraintViolationEvent value)
        constraintViolation,
    required TResult Function(ActionHeldEvent value) actionHeld,
    required TResult Function(ActionResolvedEvent value) actionResolved,
    required TResult Function(TrustEntryAddedEvent value) trustEntryAdded,
    required TResult Function(HeartbeatEvent value) heartbeat,
    required TResult Function(ErrorEvent value) error,
  }) {
    return sessionEnded(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(SessionCreatedEvent value)? sessionCreated,
    TResult? Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult? Function(SessionEndedEvent value)? sessionEnded,
    TResult? Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult? Function(ConstraintViolationEvent value)? constraintViolation,
    TResult? Function(ActionHeldEvent value)? actionHeld,
    TResult? Function(ActionResolvedEvent value)? actionResolved,
    TResult? Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult? Function(HeartbeatEvent value)? heartbeat,
    TResult? Function(ErrorEvent value)? error,
  }) {
    return sessionEnded?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(SessionCreatedEvent value)? sessionCreated,
    TResult Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult Function(SessionEndedEvent value)? sessionEnded,
    TResult Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult Function(ConstraintViolationEvent value)? constraintViolation,
    TResult Function(ActionHeldEvent value)? actionHeld,
    TResult Function(ActionResolvedEvent value)? actionResolved,
    TResult Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult Function(HeartbeatEvent value)? heartbeat,
    TResult Function(ErrorEvent value)? error,
    required TResult orElse(),
  }) {
    if (sessionEnded != null) {
      return sessionEnded(this);
    }
    return orElse();
  }

  @override
  Map<String, dynamic> toJson() {
    return _$$SessionEndedEventImplToJson(
      this,
    );
  }
}

abstract class SessionEndedEvent implements WebSocketEvent {
  const factory SessionEndedEvent(final String sessionId) =
      _$SessionEndedEventImpl;

  factory SessionEndedEvent.fromJson(Map<String, dynamic> json) =
      _$SessionEndedEventImpl.fromJson;

  String get sessionId;

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$SessionEndedEventImplCopyWith<_$SessionEndedEventImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$ConstraintUpdatedEventImplCopyWith<$Res> {
  factory _$$ConstraintUpdatedEventImplCopyWith(
          _$ConstraintUpdatedEventImpl value,
          $Res Function(_$ConstraintUpdatedEventImpl) then) =
      __$$ConstraintUpdatedEventImplCopyWithImpl<$Res>;
  @useResult
  $Res call({String sessionId, ConstraintSet constraints});

  $ConstraintSetCopyWith<$Res> get constraints;
}

/// @nodoc
class __$$ConstraintUpdatedEventImplCopyWithImpl<$Res>
    extends _$WebSocketEventCopyWithImpl<$Res, _$ConstraintUpdatedEventImpl>
    implements _$$ConstraintUpdatedEventImplCopyWith<$Res> {
  __$$ConstraintUpdatedEventImplCopyWithImpl(
      _$ConstraintUpdatedEventImpl _value,
      $Res Function(_$ConstraintUpdatedEventImpl) _then)
      : super(_value, _then);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sessionId = null,
    Object? constraints = null,
  }) {
    return _then(_$ConstraintUpdatedEventImpl(
      sessionId: null == sessionId
          ? _value.sessionId
          : sessionId // ignore: cast_nullable_to_non_nullable
              as String,
      constraints: null == constraints
          ? _value.constraints
          : constraints // ignore: cast_nullable_to_non_nullable
              as ConstraintSet,
    ));
  }

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $ConstraintSetCopyWith<$Res> get constraints {
    return $ConstraintSetCopyWith<$Res>(_value.constraints, (value) {
      return _then(_value.copyWith(constraints: value));
    });
  }
}

/// @nodoc
@JsonSerializable()
class _$ConstraintUpdatedEventImpl implements ConstraintUpdatedEvent {
  const _$ConstraintUpdatedEventImpl(
      {required this.sessionId, required this.constraints, final String? $type})
      : $type = $type ?? 'constraintUpdated';

  factory _$ConstraintUpdatedEventImpl.fromJson(Map<String, dynamic> json) =>
      _$$ConstraintUpdatedEventImplFromJson(json);

  @override
  final String sessionId;
  @override
  final ConstraintSet constraints;

  @JsonKey(name: 'runtimeType')
  final String $type;

  @override
  String toString() {
    return 'WebSocketEvent.constraintUpdated(sessionId: $sessionId, constraints: $constraints)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ConstraintUpdatedEventImpl &&
            (identical(other.sessionId, sessionId) ||
                other.sessionId == sessionId) &&
            (identical(other.constraints, constraints) ||
                other.constraints == constraints));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, sessionId, constraints);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ConstraintUpdatedEventImplCopyWith<_$ConstraintUpdatedEventImpl>
      get copyWith => __$$ConstraintUpdatedEventImplCopyWithImpl<
          _$ConstraintUpdatedEventImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(Session session) sessionCreated,
    required TResult Function(Session session) sessionUpdated,
    required TResult Function(String sessionId) sessionEnded,
    required TResult Function(String sessionId, ConstraintSet constraints)
        constraintUpdated,
    required TResult Function(
            String sessionId, String dimension, String description)
        constraintViolation,
    required TResult Function(HeldAction action) actionHeld,
    required TResult Function(HeldAction action) actionResolved,
    required TResult Function(String sessionId, TrustEntry entry)
        trustEntryAdded,
    required TResult Function() heartbeat,
    required TResult Function(String message) error,
  }) {
    return constraintUpdated(sessionId, constraints);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(Session session)? sessionCreated,
    TResult? Function(Session session)? sessionUpdated,
    TResult? Function(String sessionId)? sessionEnded,
    TResult? Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult? Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult? Function(HeldAction action)? actionHeld,
    TResult? Function(HeldAction action)? actionResolved,
    TResult? Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult? Function()? heartbeat,
    TResult? Function(String message)? error,
  }) {
    return constraintUpdated?.call(sessionId, constraints);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(Session session)? sessionCreated,
    TResult Function(Session session)? sessionUpdated,
    TResult Function(String sessionId)? sessionEnded,
    TResult Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult Function(HeldAction action)? actionHeld,
    TResult Function(HeldAction action)? actionResolved,
    TResult Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult Function()? heartbeat,
    TResult Function(String message)? error,
    required TResult orElse(),
  }) {
    if (constraintUpdated != null) {
      return constraintUpdated(sessionId, constraints);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(SessionCreatedEvent value) sessionCreated,
    required TResult Function(SessionUpdatedEvent value) sessionUpdated,
    required TResult Function(SessionEndedEvent value) sessionEnded,
    required TResult Function(ConstraintUpdatedEvent value) constraintUpdated,
    required TResult Function(ConstraintViolationEvent value)
        constraintViolation,
    required TResult Function(ActionHeldEvent value) actionHeld,
    required TResult Function(ActionResolvedEvent value) actionResolved,
    required TResult Function(TrustEntryAddedEvent value) trustEntryAdded,
    required TResult Function(HeartbeatEvent value) heartbeat,
    required TResult Function(ErrorEvent value) error,
  }) {
    return constraintUpdated(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(SessionCreatedEvent value)? sessionCreated,
    TResult? Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult? Function(SessionEndedEvent value)? sessionEnded,
    TResult? Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult? Function(ConstraintViolationEvent value)? constraintViolation,
    TResult? Function(ActionHeldEvent value)? actionHeld,
    TResult? Function(ActionResolvedEvent value)? actionResolved,
    TResult? Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult? Function(HeartbeatEvent value)? heartbeat,
    TResult? Function(ErrorEvent value)? error,
  }) {
    return constraintUpdated?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(SessionCreatedEvent value)? sessionCreated,
    TResult Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult Function(SessionEndedEvent value)? sessionEnded,
    TResult Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult Function(ConstraintViolationEvent value)? constraintViolation,
    TResult Function(ActionHeldEvent value)? actionHeld,
    TResult Function(ActionResolvedEvent value)? actionResolved,
    TResult Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult Function(HeartbeatEvent value)? heartbeat,
    TResult Function(ErrorEvent value)? error,
    required TResult orElse(),
  }) {
    if (constraintUpdated != null) {
      return constraintUpdated(this);
    }
    return orElse();
  }

  @override
  Map<String, dynamic> toJson() {
    return _$$ConstraintUpdatedEventImplToJson(
      this,
    );
  }
}

abstract class ConstraintUpdatedEvent implements WebSocketEvent {
  const factory ConstraintUpdatedEvent(
      {required final String sessionId,
      required final ConstraintSet constraints}) = _$ConstraintUpdatedEventImpl;

  factory ConstraintUpdatedEvent.fromJson(Map<String, dynamic> json) =
      _$ConstraintUpdatedEventImpl.fromJson;

  String get sessionId;
  ConstraintSet get constraints;

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ConstraintUpdatedEventImplCopyWith<_$ConstraintUpdatedEventImpl>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$ConstraintViolationEventImplCopyWith<$Res> {
  factory _$$ConstraintViolationEventImplCopyWith(
          _$ConstraintViolationEventImpl value,
          $Res Function(_$ConstraintViolationEventImpl) then) =
      __$$ConstraintViolationEventImplCopyWithImpl<$Res>;
  @useResult
  $Res call({String sessionId, String dimension, String description});
}

/// @nodoc
class __$$ConstraintViolationEventImplCopyWithImpl<$Res>
    extends _$WebSocketEventCopyWithImpl<$Res, _$ConstraintViolationEventImpl>
    implements _$$ConstraintViolationEventImplCopyWith<$Res> {
  __$$ConstraintViolationEventImplCopyWithImpl(
      _$ConstraintViolationEventImpl _value,
      $Res Function(_$ConstraintViolationEventImpl) _then)
      : super(_value, _then);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sessionId = null,
    Object? dimension = null,
    Object? description = null,
  }) {
    return _then(_$ConstraintViolationEventImpl(
      sessionId: null == sessionId
          ? _value.sessionId
          : sessionId // ignore: cast_nullable_to_non_nullable
              as String,
      dimension: null == dimension
          ? _value.dimension
          : dimension // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ConstraintViolationEventImpl implements ConstraintViolationEvent {
  const _$ConstraintViolationEventImpl(
      {required this.sessionId,
      required this.dimension,
      required this.description,
      final String? $type})
      : $type = $type ?? 'constraintViolation';

  factory _$ConstraintViolationEventImpl.fromJson(Map<String, dynamic> json) =>
      _$$ConstraintViolationEventImplFromJson(json);

  @override
  final String sessionId;
  @override
  final String dimension;
  @override
  final String description;

  @JsonKey(name: 'runtimeType')
  final String $type;

  @override
  String toString() {
    return 'WebSocketEvent.constraintViolation(sessionId: $sessionId, dimension: $dimension, description: $description)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ConstraintViolationEventImpl &&
            (identical(other.sessionId, sessionId) ||
                other.sessionId == sessionId) &&
            (identical(other.dimension, dimension) ||
                other.dimension == dimension) &&
            (identical(other.description, description) ||
                other.description == description));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, sessionId, dimension, description);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ConstraintViolationEventImplCopyWith<_$ConstraintViolationEventImpl>
      get copyWith => __$$ConstraintViolationEventImplCopyWithImpl<
          _$ConstraintViolationEventImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(Session session) sessionCreated,
    required TResult Function(Session session) sessionUpdated,
    required TResult Function(String sessionId) sessionEnded,
    required TResult Function(String sessionId, ConstraintSet constraints)
        constraintUpdated,
    required TResult Function(
            String sessionId, String dimension, String description)
        constraintViolation,
    required TResult Function(HeldAction action) actionHeld,
    required TResult Function(HeldAction action) actionResolved,
    required TResult Function(String sessionId, TrustEntry entry)
        trustEntryAdded,
    required TResult Function() heartbeat,
    required TResult Function(String message) error,
  }) {
    return constraintViolation(sessionId, dimension, description);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(Session session)? sessionCreated,
    TResult? Function(Session session)? sessionUpdated,
    TResult? Function(String sessionId)? sessionEnded,
    TResult? Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult? Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult? Function(HeldAction action)? actionHeld,
    TResult? Function(HeldAction action)? actionResolved,
    TResult? Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult? Function()? heartbeat,
    TResult? Function(String message)? error,
  }) {
    return constraintViolation?.call(sessionId, dimension, description);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(Session session)? sessionCreated,
    TResult Function(Session session)? sessionUpdated,
    TResult Function(String sessionId)? sessionEnded,
    TResult Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult Function(HeldAction action)? actionHeld,
    TResult Function(HeldAction action)? actionResolved,
    TResult Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult Function()? heartbeat,
    TResult Function(String message)? error,
    required TResult orElse(),
  }) {
    if (constraintViolation != null) {
      return constraintViolation(sessionId, dimension, description);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(SessionCreatedEvent value) sessionCreated,
    required TResult Function(SessionUpdatedEvent value) sessionUpdated,
    required TResult Function(SessionEndedEvent value) sessionEnded,
    required TResult Function(ConstraintUpdatedEvent value) constraintUpdated,
    required TResult Function(ConstraintViolationEvent value)
        constraintViolation,
    required TResult Function(ActionHeldEvent value) actionHeld,
    required TResult Function(ActionResolvedEvent value) actionResolved,
    required TResult Function(TrustEntryAddedEvent value) trustEntryAdded,
    required TResult Function(HeartbeatEvent value) heartbeat,
    required TResult Function(ErrorEvent value) error,
  }) {
    return constraintViolation(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(SessionCreatedEvent value)? sessionCreated,
    TResult? Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult? Function(SessionEndedEvent value)? sessionEnded,
    TResult? Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult? Function(ConstraintViolationEvent value)? constraintViolation,
    TResult? Function(ActionHeldEvent value)? actionHeld,
    TResult? Function(ActionResolvedEvent value)? actionResolved,
    TResult? Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult? Function(HeartbeatEvent value)? heartbeat,
    TResult? Function(ErrorEvent value)? error,
  }) {
    return constraintViolation?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(SessionCreatedEvent value)? sessionCreated,
    TResult Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult Function(SessionEndedEvent value)? sessionEnded,
    TResult Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult Function(ConstraintViolationEvent value)? constraintViolation,
    TResult Function(ActionHeldEvent value)? actionHeld,
    TResult Function(ActionResolvedEvent value)? actionResolved,
    TResult Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult Function(HeartbeatEvent value)? heartbeat,
    TResult Function(ErrorEvent value)? error,
    required TResult orElse(),
  }) {
    if (constraintViolation != null) {
      return constraintViolation(this);
    }
    return orElse();
  }

  @override
  Map<String, dynamic> toJson() {
    return _$$ConstraintViolationEventImplToJson(
      this,
    );
  }
}

abstract class ConstraintViolationEvent implements WebSocketEvent {
  const factory ConstraintViolationEvent(
      {required final String sessionId,
      required final String dimension,
      required final String description}) = _$ConstraintViolationEventImpl;

  factory ConstraintViolationEvent.fromJson(Map<String, dynamic> json) =
      _$ConstraintViolationEventImpl.fromJson;

  String get sessionId;
  String get dimension;
  String get description;

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ConstraintViolationEventImplCopyWith<_$ConstraintViolationEventImpl>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$ActionHeldEventImplCopyWith<$Res> {
  factory _$$ActionHeldEventImplCopyWith(_$ActionHeldEventImpl value,
          $Res Function(_$ActionHeldEventImpl) then) =
      __$$ActionHeldEventImplCopyWithImpl<$Res>;
  @useResult
  $Res call({HeldAction action});

  $HeldActionCopyWith<$Res> get action;
}

/// @nodoc
class __$$ActionHeldEventImplCopyWithImpl<$Res>
    extends _$WebSocketEventCopyWithImpl<$Res, _$ActionHeldEventImpl>
    implements _$$ActionHeldEventImplCopyWith<$Res> {
  __$$ActionHeldEventImplCopyWithImpl(
      _$ActionHeldEventImpl _value, $Res Function(_$ActionHeldEventImpl) _then)
      : super(_value, _then);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? action = null,
  }) {
    return _then(_$ActionHeldEventImpl(
      null == action
          ? _value.action
          : action // ignore: cast_nullable_to_non_nullable
              as HeldAction,
    ));
  }

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $HeldActionCopyWith<$Res> get action {
    return $HeldActionCopyWith<$Res>(_value.action, (value) {
      return _then(_value.copyWith(action: value));
    });
  }
}

/// @nodoc
@JsonSerializable()
class _$ActionHeldEventImpl implements ActionHeldEvent {
  const _$ActionHeldEventImpl(this.action, {final String? $type})
      : $type = $type ?? 'actionHeld';

  factory _$ActionHeldEventImpl.fromJson(Map<String, dynamic> json) =>
      _$$ActionHeldEventImplFromJson(json);

  @override
  final HeldAction action;

  @JsonKey(name: 'runtimeType')
  final String $type;

  @override
  String toString() {
    return 'WebSocketEvent.actionHeld(action: $action)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ActionHeldEventImpl &&
            (identical(other.action, action) || other.action == action));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, action);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ActionHeldEventImplCopyWith<_$ActionHeldEventImpl> get copyWith =>
      __$$ActionHeldEventImplCopyWithImpl<_$ActionHeldEventImpl>(
          this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(Session session) sessionCreated,
    required TResult Function(Session session) sessionUpdated,
    required TResult Function(String sessionId) sessionEnded,
    required TResult Function(String sessionId, ConstraintSet constraints)
        constraintUpdated,
    required TResult Function(
            String sessionId, String dimension, String description)
        constraintViolation,
    required TResult Function(HeldAction action) actionHeld,
    required TResult Function(HeldAction action) actionResolved,
    required TResult Function(String sessionId, TrustEntry entry)
        trustEntryAdded,
    required TResult Function() heartbeat,
    required TResult Function(String message) error,
  }) {
    return actionHeld(action);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(Session session)? sessionCreated,
    TResult? Function(Session session)? sessionUpdated,
    TResult? Function(String sessionId)? sessionEnded,
    TResult? Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult? Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult? Function(HeldAction action)? actionHeld,
    TResult? Function(HeldAction action)? actionResolved,
    TResult? Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult? Function()? heartbeat,
    TResult? Function(String message)? error,
  }) {
    return actionHeld?.call(action);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(Session session)? sessionCreated,
    TResult Function(Session session)? sessionUpdated,
    TResult Function(String sessionId)? sessionEnded,
    TResult Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult Function(HeldAction action)? actionHeld,
    TResult Function(HeldAction action)? actionResolved,
    TResult Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult Function()? heartbeat,
    TResult Function(String message)? error,
    required TResult orElse(),
  }) {
    if (actionHeld != null) {
      return actionHeld(action);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(SessionCreatedEvent value) sessionCreated,
    required TResult Function(SessionUpdatedEvent value) sessionUpdated,
    required TResult Function(SessionEndedEvent value) sessionEnded,
    required TResult Function(ConstraintUpdatedEvent value) constraintUpdated,
    required TResult Function(ConstraintViolationEvent value)
        constraintViolation,
    required TResult Function(ActionHeldEvent value) actionHeld,
    required TResult Function(ActionResolvedEvent value) actionResolved,
    required TResult Function(TrustEntryAddedEvent value) trustEntryAdded,
    required TResult Function(HeartbeatEvent value) heartbeat,
    required TResult Function(ErrorEvent value) error,
  }) {
    return actionHeld(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(SessionCreatedEvent value)? sessionCreated,
    TResult? Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult? Function(SessionEndedEvent value)? sessionEnded,
    TResult? Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult? Function(ConstraintViolationEvent value)? constraintViolation,
    TResult? Function(ActionHeldEvent value)? actionHeld,
    TResult? Function(ActionResolvedEvent value)? actionResolved,
    TResult? Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult? Function(HeartbeatEvent value)? heartbeat,
    TResult? Function(ErrorEvent value)? error,
  }) {
    return actionHeld?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(SessionCreatedEvent value)? sessionCreated,
    TResult Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult Function(SessionEndedEvent value)? sessionEnded,
    TResult Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult Function(ConstraintViolationEvent value)? constraintViolation,
    TResult Function(ActionHeldEvent value)? actionHeld,
    TResult Function(ActionResolvedEvent value)? actionResolved,
    TResult Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult Function(HeartbeatEvent value)? heartbeat,
    TResult Function(ErrorEvent value)? error,
    required TResult orElse(),
  }) {
    if (actionHeld != null) {
      return actionHeld(this);
    }
    return orElse();
  }

  @override
  Map<String, dynamic> toJson() {
    return _$$ActionHeldEventImplToJson(
      this,
    );
  }
}

abstract class ActionHeldEvent implements WebSocketEvent {
  const factory ActionHeldEvent(final HeldAction action) =
      _$ActionHeldEventImpl;

  factory ActionHeldEvent.fromJson(Map<String, dynamic> json) =
      _$ActionHeldEventImpl.fromJson;

  HeldAction get action;

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ActionHeldEventImplCopyWith<_$ActionHeldEventImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$ActionResolvedEventImplCopyWith<$Res> {
  factory _$$ActionResolvedEventImplCopyWith(_$ActionResolvedEventImpl value,
          $Res Function(_$ActionResolvedEventImpl) then) =
      __$$ActionResolvedEventImplCopyWithImpl<$Res>;
  @useResult
  $Res call({HeldAction action});

  $HeldActionCopyWith<$Res> get action;
}

/// @nodoc
class __$$ActionResolvedEventImplCopyWithImpl<$Res>
    extends _$WebSocketEventCopyWithImpl<$Res, _$ActionResolvedEventImpl>
    implements _$$ActionResolvedEventImplCopyWith<$Res> {
  __$$ActionResolvedEventImplCopyWithImpl(_$ActionResolvedEventImpl _value,
      $Res Function(_$ActionResolvedEventImpl) _then)
      : super(_value, _then);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? action = null,
  }) {
    return _then(_$ActionResolvedEventImpl(
      null == action
          ? _value.action
          : action // ignore: cast_nullable_to_non_nullable
              as HeldAction,
    ));
  }

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $HeldActionCopyWith<$Res> get action {
    return $HeldActionCopyWith<$Res>(_value.action, (value) {
      return _then(_value.copyWith(action: value));
    });
  }
}

/// @nodoc
@JsonSerializable()
class _$ActionResolvedEventImpl implements ActionResolvedEvent {
  const _$ActionResolvedEventImpl(this.action, {final String? $type})
      : $type = $type ?? 'actionResolved';

  factory _$ActionResolvedEventImpl.fromJson(Map<String, dynamic> json) =>
      _$$ActionResolvedEventImplFromJson(json);

  @override
  final HeldAction action;

  @JsonKey(name: 'runtimeType')
  final String $type;

  @override
  String toString() {
    return 'WebSocketEvent.actionResolved(action: $action)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ActionResolvedEventImpl &&
            (identical(other.action, action) || other.action == action));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, action);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ActionResolvedEventImplCopyWith<_$ActionResolvedEventImpl> get copyWith =>
      __$$ActionResolvedEventImplCopyWithImpl<_$ActionResolvedEventImpl>(
          this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(Session session) sessionCreated,
    required TResult Function(Session session) sessionUpdated,
    required TResult Function(String sessionId) sessionEnded,
    required TResult Function(String sessionId, ConstraintSet constraints)
        constraintUpdated,
    required TResult Function(
            String sessionId, String dimension, String description)
        constraintViolation,
    required TResult Function(HeldAction action) actionHeld,
    required TResult Function(HeldAction action) actionResolved,
    required TResult Function(String sessionId, TrustEntry entry)
        trustEntryAdded,
    required TResult Function() heartbeat,
    required TResult Function(String message) error,
  }) {
    return actionResolved(action);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(Session session)? sessionCreated,
    TResult? Function(Session session)? sessionUpdated,
    TResult? Function(String sessionId)? sessionEnded,
    TResult? Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult? Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult? Function(HeldAction action)? actionHeld,
    TResult? Function(HeldAction action)? actionResolved,
    TResult? Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult? Function()? heartbeat,
    TResult? Function(String message)? error,
  }) {
    return actionResolved?.call(action);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(Session session)? sessionCreated,
    TResult Function(Session session)? sessionUpdated,
    TResult Function(String sessionId)? sessionEnded,
    TResult Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult Function(HeldAction action)? actionHeld,
    TResult Function(HeldAction action)? actionResolved,
    TResult Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult Function()? heartbeat,
    TResult Function(String message)? error,
    required TResult orElse(),
  }) {
    if (actionResolved != null) {
      return actionResolved(action);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(SessionCreatedEvent value) sessionCreated,
    required TResult Function(SessionUpdatedEvent value) sessionUpdated,
    required TResult Function(SessionEndedEvent value) sessionEnded,
    required TResult Function(ConstraintUpdatedEvent value) constraintUpdated,
    required TResult Function(ConstraintViolationEvent value)
        constraintViolation,
    required TResult Function(ActionHeldEvent value) actionHeld,
    required TResult Function(ActionResolvedEvent value) actionResolved,
    required TResult Function(TrustEntryAddedEvent value) trustEntryAdded,
    required TResult Function(HeartbeatEvent value) heartbeat,
    required TResult Function(ErrorEvent value) error,
  }) {
    return actionResolved(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(SessionCreatedEvent value)? sessionCreated,
    TResult? Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult? Function(SessionEndedEvent value)? sessionEnded,
    TResult? Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult? Function(ConstraintViolationEvent value)? constraintViolation,
    TResult? Function(ActionHeldEvent value)? actionHeld,
    TResult? Function(ActionResolvedEvent value)? actionResolved,
    TResult? Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult? Function(HeartbeatEvent value)? heartbeat,
    TResult? Function(ErrorEvent value)? error,
  }) {
    return actionResolved?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(SessionCreatedEvent value)? sessionCreated,
    TResult Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult Function(SessionEndedEvent value)? sessionEnded,
    TResult Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult Function(ConstraintViolationEvent value)? constraintViolation,
    TResult Function(ActionHeldEvent value)? actionHeld,
    TResult Function(ActionResolvedEvent value)? actionResolved,
    TResult Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult Function(HeartbeatEvent value)? heartbeat,
    TResult Function(ErrorEvent value)? error,
    required TResult orElse(),
  }) {
    if (actionResolved != null) {
      return actionResolved(this);
    }
    return orElse();
  }

  @override
  Map<String, dynamic> toJson() {
    return _$$ActionResolvedEventImplToJson(
      this,
    );
  }
}

abstract class ActionResolvedEvent implements WebSocketEvent {
  const factory ActionResolvedEvent(final HeldAction action) =
      _$ActionResolvedEventImpl;

  factory ActionResolvedEvent.fromJson(Map<String, dynamic> json) =
      _$ActionResolvedEventImpl.fromJson;

  HeldAction get action;

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ActionResolvedEventImplCopyWith<_$ActionResolvedEventImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$TrustEntryAddedEventImplCopyWith<$Res> {
  factory _$$TrustEntryAddedEventImplCopyWith(_$TrustEntryAddedEventImpl value,
          $Res Function(_$TrustEntryAddedEventImpl) then) =
      __$$TrustEntryAddedEventImplCopyWithImpl<$Res>;
  @useResult
  $Res call({String sessionId, TrustEntry entry});

  $TrustEntryCopyWith<$Res> get entry;
}

/// @nodoc
class __$$TrustEntryAddedEventImplCopyWithImpl<$Res>
    extends _$WebSocketEventCopyWithImpl<$Res, _$TrustEntryAddedEventImpl>
    implements _$$TrustEntryAddedEventImplCopyWith<$Res> {
  __$$TrustEntryAddedEventImplCopyWithImpl(_$TrustEntryAddedEventImpl _value,
      $Res Function(_$TrustEntryAddedEventImpl) _then)
      : super(_value, _then);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sessionId = null,
    Object? entry = null,
  }) {
    return _then(_$TrustEntryAddedEventImpl(
      sessionId: null == sessionId
          ? _value.sessionId
          : sessionId // ignore: cast_nullable_to_non_nullable
              as String,
      entry: null == entry
          ? _value.entry
          : entry // ignore: cast_nullable_to_non_nullable
              as TrustEntry,
    ));
  }

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $TrustEntryCopyWith<$Res> get entry {
    return $TrustEntryCopyWith<$Res>(_value.entry, (value) {
      return _then(_value.copyWith(entry: value));
    });
  }
}

/// @nodoc
@JsonSerializable()
class _$TrustEntryAddedEventImpl implements TrustEntryAddedEvent {
  const _$TrustEntryAddedEventImpl(
      {required this.sessionId, required this.entry, final String? $type})
      : $type = $type ?? 'trustEntryAdded';

  factory _$TrustEntryAddedEventImpl.fromJson(Map<String, dynamic> json) =>
      _$$TrustEntryAddedEventImplFromJson(json);

  @override
  final String sessionId;
  @override
  final TrustEntry entry;

  @JsonKey(name: 'runtimeType')
  final String $type;

  @override
  String toString() {
    return 'WebSocketEvent.trustEntryAdded(sessionId: $sessionId, entry: $entry)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$TrustEntryAddedEventImpl &&
            (identical(other.sessionId, sessionId) ||
                other.sessionId == sessionId) &&
            (identical(other.entry, entry) || other.entry == entry));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, sessionId, entry);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$TrustEntryAddedEventImplCopyWith<_$TrustEntryAddedEventImpl>
      get copyWith =>
          __$$TrustEntryAddedEventImplCopyWithImpl<_$TrustEntryAddedEventImpl>(
              this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(Session session) sessionCreated,
    required TResult Function(Session session) sessionUpdated,
    required TResult Function(String sessionId) sessionEnded,
    required TResult Function(String sessionId, ConstraintSet constraints)
        constraintUpdated,
    required TResult Function(
            String sessionId, String dimension, String description)
        constraintViolation,
    required TResult Function(HeldAction action) actionHeld,
    required TResult Function(HeldAction action) actionResolved,
    required TResult Function(String sessionId, TrustEntry entry)
        trustEntryAdded,
    required TResult Function() heartbeat,
    required TResult Function(String message) error,
  }) {
    return trustEntryAdded(sessionId, entry);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(Session session)? sessionCreated,
    TResult? Function(Session session)? sessionUpdated,
    TResult? Function(String sessionId)? sessionEnded,
    TResult? Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult? Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult? Function(HeldAction action)? actionHeld,
    TResult? Function(HeldAction action)? actionResolved,
    TResult? Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult? Function()? heartbeat,
    TResult? Function(String message)? error,
  }) {
    return trustEntryAdded?.call(sessionId, entry);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(Session session)? sessionCreated,
    TResult Function(Session session)? sessionUpdated,
    TResult Function(String sessionId)? sessionEnded,
    TResult Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult Function(HeldAction action)? actionHeld,
    TResult Function(HeldAction action)? actionResolved,
    TResult Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult Function()? heartbeat,
    TResult Function(String message)? error,
    required TResult orElse(),
  }) {
    if (trustEntryAdded != null) {
      return trustEntryAdded(sessionId, entry);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(SessionCreatedEvent value) sessionCreated,
    required TResult Function(SessionUpdatedEvent value) sessionUpdated,
    required TResult Function(SessionEndedEvent value) sessionEnded,
    required TResult Function(ConstraintUpdatedEvent value) constraintUpdated,
    required TResult Function(ConstraintViolationEvent value)
        constraintViolation,
    required TResult Function(ActionHeldEvent value) actionHeld,
    required TResult Function(ActionResolvedEvent value) actionResolved,
    required TResult Function(TrustEntryAddedEvent value) trustEntryAdded,
    required TResult Function(HeartbeatEvent value) heartbeat,
    required TResult Function(ErrorEvent value) error,
  }) {
    return trustEntryAdded(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(SessionCreatedEvent value)? sessionCreated,
    TResult? Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult? Function(SessionEndedEvent value)? sessionEnded,
    TResult? Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult? Function(ConstraintViolationEvent value)? constraintViolation,
    TResult? Function(ActionHeldEvent value)? actionHeld,
    TResult? Function(ActionResolvedEvent value)? actionResolved,
    TResult? Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult? Function(HeartbeatEvent value)? heartbeat,
    TResult? Function(ErrorEvent value)? error,
  }) {
    return trustEntryAdded?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(SessionCreatedEvent value)? sessionCreated,
    TResult Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult Function(SessionEndedEvent value)? sessionEnded,
    TResult Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult Function(ConstraintViolationEvent value)? constraintViolation,
    TResult Function(ActionHeldEvent value)? actionHeld,
    TResult Function(ActionResolvedEvent value)? actionResolved,
    TResult Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult Function(HeartbeatEvent value)? heartbeat,
    TResult Function(ErrorEvent value)? error,
    required TResult orElse(),
  }) {
    if (trustEntryAdded != null) {
      return trustEntryAdded(this);
    }
    return orElse();
  }

  @override
  Map<String, dynamic> toJson() {
    return _$$TrustEntryAddedEventImplToJson(
      this,
    );
  }
}

abstract class TrustEntryAddedEvent implements WebSocketEvent {
  const factory TrustEntryAddedEvent(
      {required final String sessionId,
      required final TrustEntry entry}) = _$TrustEntryAddedEventImpl;

  factory TrustEntryAddedEvent.fromJson(Map<String, dynamic> json) =
      _$TrustEntryAddedEventImpl.fromJson;

  String get sessionId;
  TrustEntry get entry;

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$TrustEntryAddedEventImplCopyWith<_$TrustEntryAddedEventImpl>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class _$$HeartbeatEventImplCopyWith<$Res> {
  factory _$$HeartbeatEventImplCopyWith(_$HeartbeatEventImpl value,
          $Res Function(_$HeartbeatEventImpl) then) =
      __$$HeartbeatEventImplCopyWithImpl<$Res>;
}

/// @nodoc
class __$$HeartbeatEventImplCopyWithImpl<$Res>
    extends _$WebSocketEventCopyWithImpl<$Res, _$HeartbeatEventImpl>
    implements _$$HeartbeatEventImplCopyWith<$Res> {
  __$$HeartbeatEventImplCopyWithImpl(
      _$HeartbeatEventImpl _value, $Res Function(_$HeartbeatEventImpl) _then)
      : super(_value, _then);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
}

/// @nodoc
@JsonSerializable()
class _$HeartbeatEventImpl implements HeartbeatEvent {
  const _$HeartbeatEventImpl({final String? $type})
      : $type = $type ?? 'heartbeat';

  factory _$HeartbeatEventImpl.fromJson(Map<String, dynamic> json) =>
      _$$HeartbeatEventImplFromJson(json);

  @JsonKey(name: 'runtimeType')
  final String $type;

  @override
  String toString() {
    return 'WebSocketEvent.heartbeat()';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType && other is _$HeartbeatEventImpl);
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => runtimeType.hashCode;

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(Session session) sessionCreated,
    required TResult Function(Session session) sessionUpdated,
    required TResult Function(String sessionId) sessionEnded,
    required TResult Function(String sessionId, ConstraintSet constraints)
        constraintUpdated,
    required TResult Function(
            String sessionId, String dimension, String description)
        constraintViolation,
    required TResult Function(HeldAction action) actionHeld,
    required TResult Function(HeldAction action) actionResolved,
    required TResult Function(String sessionId, TrustEntry entry)
        trustEntryAdded,
    required TResult Function() heartbeat,
    required TResult Function(String message) error,
  }) {
    return heartbeat();
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(Session session)? sessionCreated,
    TResult? Function(Session session)? sessionUpdated,
    TResult? Function(String sessionId)? sessionEnded,
    TResult? Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult? Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult? Function(HeldAction action)? actionHeld,
    TResult? Function(HeldAction action)? actionResolved,
    TResult? Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult? Function()? heartbeat,
    TResult? Function(String message)? error,
  }) {
    return heartbeat?.call();
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(Session session)? sessionCreated,
    TResult Function(Session session)? sessionUpdated,
    TResult Function(String sessionId)? sessionEnded,
    TResult Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult Function(HeldAction action)? actionHeld,
    TResult Function(HeldAction action)? actionResolved,
    TResult Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult Function()? heartbeat,
    TResult Function(String message)? error,
    required TResult orElse(),
  }) {
    if (heartbeat != null) {
      return heartbeat();
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(SessionCreatedEvent value) sessionCreated,
    required TResult Function(SessionUpdatedEvent value) sessionUpdated,
    required TResult Function(SessionEndedEvent value) sessionEnded,
    required TResult Function(ConstraintUpdatedEvent value) constraintUpdated,
    required TResult Function(ConstraintViolationEvent value)
        constraintViolation,
    required TResult Function(ActionHeldEvent value) actionHeld,
    required TResult Function(ActionResolvedEvent value) actionResolved,
    required TResult Function(TrustEntryAddedEvent value) trustEntryAdded,
    required TResult Function(HeartbeatEvent value) heartbeat,
    required TResult Function(ErrorEvent value) error,
  }) {
    return heartbeat(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(SessionCreatedEvent value)? sessionCreated,
    TResult? Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult? Function(SessionEndedEvent value)? sessionEnded,
    TResult? Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult? Function(ConstraintViolationEvent value)? constraintViolation,
    TResult? Function(ActionHeldEvent value)? actionHeld,
    TResult? Function(ActionResolvedEvent value)? actionResolved,
    TResult? Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult? Function(HeartbeatEvent value)? heartbeat,
    TResult? Function(ErrorEvent value)? error,
  }) {
    return heartbeat?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(SessionCreatedEvent value)? sessionCreated,
    TResult Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult Function(SessionEndedEvent value)? sessionEnded,
    TResult Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult Function(ConstraintViolationEvent value)? constraintViolation,
    TResult Function(ActionHeldEvent value)? actionHeld,
    TResult Function(ActionResolvedEvent value)? actionResolved,
    TResult Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult Function(HeartbeatEvent value)? heartbeat,
    TResult Function(ErrorEvent value)? error,
    required TResult orElse(),
  }) {
    if (heartbeat != null) {
      return heartbeat(this);
    }
    return orElse();
  }

  @override
  Map<String, dynamic> toJson() {
    return _$$HeartbeatEventImplToJson(
      this,
    );
  }
}

abstract class HeartbeatEvent implements WebSocketEvent {
  const factory HeartbeatEvent() = _$HeartbeatEventImpl;

  factory HeartbeatEvent.fromJson(Map<String, dynamic> json) =
      _$HeartbeatEventImpl.fromJson;
}

/// @nodoc
abstract class _$$ErrorEventImplCopyWith<$Res> {
  factory _$$ErrorEventImplCopyWith(
          _$ErrorEventImpl value, $Res Function(_$ErrorEventImpl) then) =
      __$$ErrorEventImplCopyWithImpl<$Res>;
  @useResult
  $Res call({String message});
}

/// @nodoc
class __$$ErrorEventImplCopyWithImpl<$Res>
    extends _$WebSocketEventCopyWithImpl<$Res, _$ErrorEventImpl>
    implements _$$ErrorEventImplCopyWith<$Res> {
  __$$ErrorEventImplCopyWithImpl(
      _$ErrorEventImpl _value, $Res Function(_$ErrorEventImpl) _then)
      : super(_value, _then);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? message = null,
  }) {
    return _then(_$ErrorEventImpl(
      message: null == message
          ? _value.message
          : message // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ErrorEventImpl implements ErrorEvent {
  const _$ErrorEventImpl({required this.message, final String? $type})
      : $type = $type ?? 'error';

  factory _$ErrorEventImpl.fromJson(Map<String, dynamic> json) =>
      _$$ErrorEventImplFromJson(json);

  @override
  final String message;

  @JsonKey(name: 'runtimeType')
  final String $type;

  @override
  String toString() {
    return 'WebSocketEvent.error(message: $message)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ErrorEventImpl &&
            (identical(other.message, message) || other.message == message));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, message);

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ErrorEventImplCopyWith<_$ErrorEventImpl> get copyWith =>
      __$$ErrorEventImplCopyWithImpl<_$ErrorEventImpl>(this, _$identity);

  @override
  @optionalTypeArgs
  TResult when<TResult extends Object?>({
    required TResult Function(Session session) sessionCreated,
    required TResult Function(Session session) sessionUpdated,
    required TResult Function(String sessionId) sessionEnded,
    required TResult Function(String sessionId, ConstraintSet constraints)
        constraintUpdated,
    required TResult Function(
            String sessionId, String dimension, String description)
        constraintViolation,
    required TResult Function(HeldAction action) actionHeld,
    required TResult Function(HeldAction action) actionResolved,
    required TResult Function(String sessionId, TrustEntry entry)
        trustEntryAdded,
    required TResult Function() heartbeat,
    required TResult Function(String message) error,
  }) {
    return error(message);
  }

  @override
  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>({
    TResult? Function(Session session)? sessionCreated,
    TResult? Function(Session session)? sessionUpdated,
    TResult? Function(String sessionId)? sessionEnded,
    TResult? Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult? Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult? Function(HeldAction action)? actionHeld,
    TResult? Function(HeldAction action)? actionResolved,
    TResult? Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult? Function()? heartbeat,
    TResult? Function(String message)? error,
  }) {
    return error?.call(message);
  }

  @override
  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>({
    TResult Function(Session session)? sessionCreated,
    TResult Function(Session session)? sessionUpdated,
    TResult Function(String sessionId)? sessionEnded,
    TResult Function(String sessionId, ConstraintSet constraints)?
        constraintUpdated,
    TResult Function(String sessionId, String dimension, String description)?
        constraintViolation,
    TResult Function(HeldAction action)? actionHeld,
    TResult Function(HeldAction action)? actionResolved,
    TResult Function(String sessionId, TrustEntry entry)? trustEntryAdded,
    TResult Function()? heartbeat,
    TResult Function(String message)? error,
    required TResult orElse(),
  }) {
    if (error != null) {
      return error(message);
    }
    return orElse();
  }

  @override
  @optionalTypeArgs
  TResult map<TResult extends Object?>({
    required TResult Function(SessionCreatedEvent value) sessionCreated,
    required TResult Function(SessionUpdatedEvent value) sessionUpdated,
    required TResult Function(SessionEndedEvent value) sessionEnded,
    required TResult Function(ConstraintUpdatedEvent value) constraintUpdated,
    required TResult Function(ConstraintViolationEvent value)
        constraintViolation,
    required TResult Function(ActionHeldEvent value) actionHeld,
    required TResult Function(ActionResolvedEvent value) actionResolved,
    required TResult Function(TrustEntryAddedEvent value) trustEntryAdded,
    required TResult Function(HeartbeatEvent value) heartbeat,
    required TResult Function(ErrorEvent value) error,
  }) {
    return error(this);
  }

  @override
  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>({
    TResult? Function(SessionCreatedEvent value)? sessionCreated,
    TResult? Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult? Function(SessionEndedEvent value)? sessionEnded,
    TResult? Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult? Function(ConstraintViolationEvent value)? constraintViolation,
    TResult? Function(ActionHeldEvent value)? actionHeld,
    TResult? Function(ActionResolvedEvent value)? actionResolved,
    TResult? Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult? Function(HeartbeatEvent value)? heartbeat,
    TResult? Function(ErrorEvent value)? error,
  }) {
    return error?.call(this);
  }

  @override
  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>({
    TResult Function(SessionCreatedEvent value)? sessionCreated,
    TResult Function(SessionUpdatedEvent value)? sessionUpdated,
    TResult Function(SessionEndedEvent value)? sessionEnded,
    TResult Function(ConstraintUpdatedEvent value)? constraintUpdated,
    TResult Function(ConstraintViolationEvent value)? constraintViolation,
    TResult Function(ActionHeldEvent value)? actionHeld,
    TResult Function(ActionResolvedEvent value)? actionResolved,
    TResult Function(TrustEntryAddedEvent value)? trustEntryAdded,
    TResult Function(HeartbeatEvent value)? heartbeat,
    TResult Function(ErrorEvent value)? error,
    required TResult orElse(),
  }) {
    if (error != null) {
      return error(this);
    }
    return orElse();
  }

  @override
  Map<String, dynamic> toJson() {
    return _$$ErrorEventImplToJson(
      this,
    );
  }
}

abstract class ErrorEvent implements WebSocketEvent {
  const factory ErrorEvent({required final String message}) = _$ErrorEventImpl;

  factory ErrorEvent.fromJson(Map<String, dynamic> json) =
      _$ErrorEventImpl.fromJson;

  String get message;

  /// Create a copy of WebSocketEvent
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ErrorEventImplCopyWith<_$ErrorEventImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
