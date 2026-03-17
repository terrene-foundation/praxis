// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'api_config.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$ApiConfigImpl _$$ApiConfigImplFromJson(Map<String, dynamic> json) =>
    _$ApiConfigImpl(
      baseUrl: json['baseUrl'] as String,
      connectTimeout: json['connectTimeout'] == null
          ? const Duration(seconds: 10)
          : Duration(microseconds: (json['connectTimeout'] as num).toInt()),
      receiveTimeout: json['receiveTimeout'] == null
          ? const Duration(seconds: 30)
          : Duration(microseconds: (json['receiveTimeout'] as num).toInt()),
    );

Map<String, dynamic> _$$ApiConfigImplToJson(_$ApiConfigImpl instance) =>
    <String, dynamic>{
      'baseUrl': instance.baseUrl,
      'connectTimeout': instance.connectTimeout.inMicroseconds,
      'receiveTimeout': instance.receiveTimeout.inMicroseconds,
    };
