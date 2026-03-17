// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'websocket_events.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$SessionCreatedEventImpl _$$SessionCreatedEventImplFromJson(
        Map<String, dynamic> json) =>
    _$SessionCreatedEventImpl(
      Session.fromJson(json['session'] as Map<String, dynamic>),
      $type: json['runtimeType'] as String?,
    );

Map<String, dynamic> _$$SessionCreatedEventImplToJson(
        _$SessionCreatedEventImpl instance) =>
    <String, dynamic>{
      'session': instance.session,
      'runtimeType': instance.$type,
    };

_$SessionUpdatedEventImpl _$$SessionUpdatedEventImplFromJson(
        Map<String, dynamic> json) =>
    _$SessionUpdatedEventImpl(
      Session.fromJson(json['session'] as Map<String, dynamic>),
      $type: json['runtimeType'] as String?,
    );

Map<String, dynamic> _$$SessionUpdatedEventImplToJson(
        _$SessionUpdatedEventImpl instance) =>
    <String, dynamic>{
      'session': instance.session,
      'runtimeType': instance.$type,
    };

_$SessionEndedEventImpl _$$SessionEndedEventImplFromJson(
        Map<String, dynamic> json) =>
    _$SessionEndedEventImpl(
      json['sessionId'] as String,
      $type: json['runtimeType'] as String?,
    );

Map<String, dynamic> _$$SessionEndedEventImplToJson(
        _$SessionEndedEventImpl instance) =>
    <String, dynamic>{
      'sessionId': instance.sessionId,
      'runtimeType': instance.$type,
    };

_$ConstraintUpdatedEventImpl _$$ConstraintUpdatedEventImplFromJson(
        Map<String, dynamic> json) =>
    _$ConstraintUpdatedEventImpl(
      sessionId: json['sessionId'] as String,
      constraints:
          ConstraintSet.fromJson(json['constraints'] as Map<String, dynamic>),
      $type: json['runtimeType'] as String?,
    );

Map<String, dynamic> _$$ConstraintUpdatedEventImplToJson(
        _$ConstraintUpdatedEventImpl instance) =>
    <String, dynamic>{
      'sessionId': instance.sessionId,
      'constraints': instance.constraints,
      'runtimeType': instance.$type,
    };

_$ConstraintViolationEventImpl _$$ConstraintViolationEventImplFromJson(
        Map<String, dynamic> json) =>
    _$ConstraintViolationEventImpl(
      sessionId: json['sessionId'] as String,
      dimension: json['dimension'] as String,
      description: json['description'] as String,
      $type: json['runtimeType'] as String?,
    );

Map<String, dynamic> _$$ConstraintViolationEventImplToJson(
        _$ConstraintViolationEventImpl instance) =>
    <String, dynamic>{
      'sessionId': instance.sessionId,
      'dimension': instance.dimension,
      'description': instance.description,
      'runtimeType': instance.$type,
    };

_$ActionHeldEventImpl _$$ActionHeldEventImplFromJson(
        Map<String, dynamic> json) =>
    _$ActionHeldEventImpl(
      HeldAction.fromJson(json['action'] as Map<String, dynamic>),
      $type: json['runtimeType'] as String?,
    );

Map<String, dynamic> _$$ActionHeldEventImplToJson(
        _$ActionHeldEventImpl instance) =>
    <String, dynamic>{
      'action': instance.action,
      'runtimeType': instance.$type,
    };

_$ActionResolvedEventImpl _$$ActionResolvedEventImplFromJson(
        Map<String, dynamic> json) =>
    _$ActionResolvedEventImpl(
      HeldAction.fromJson(json['action'] as Map<String, dynamic>),
      $type: json['runtimeType'] as String?,
    );

Map<String, dynamic> _$$ActionResolvedEventImplToJson(
        _$ActionResolvedEventImpl instance) =>
    <String, dynamic>{
      'action': instance.action,
      'runtimeType': instance.$type,
    };

_$TrustEntryAddedEventImpl _$$TrustEntryAddedEventImplFromJson(
        Map<String, dynamic> json) =>
    _$TrustEntryAddedEventImpl(
      sessionId: json['sessionId'] as String,
      entry: TrustEntry.fromJson(json['entry'] as Map<String, dynamic>),
      $type: json['runtimeType'] as String?,
    );

Map<String, dynamic> _$$TrustEntryAddedEventImplToJson(
        _$TrustEntryAddedEventImpl instance) =>
    <String, dynamic>{
      'sessionId': instance.sessionId,
      'entry': instance.entry,
      'runtimeType': instance.$type,
    };

_$HeartbeatEventImpl _$$HeartbeatEventImplFromJson(Map<String, dynamic> json) =>
    _$HeartbeatEventImpl(
      $type: json['runtimeType'] as String?,
    );

Map<String, dynamic> _$$HeartbeatEventImplToJson(
        _$HeartbeatEventImpl instance) =>
    <String, dynamic>{
      'runtimeType': instance.$type,
    };

_$ErrorEventImpl _$$ErrorEventImplFromJson(Map<String, dynamic> json) =>
    _$ErrorEventImpl(
      message: json['message'] as String,
      $type: json['runtimeType'] as String?,
    );

Map<String, dynamic> _$$ErrorEventImplToJson(_$ErrorEventImpl instance) =>
    <String, dynamic>{
      'message': instance.message,
      'runtimeType': instance.$type,
    };
