import 'package:freezed_annotation/freezed_annotation.dart';

part 'api_config.freezed.dart';
part 'api_config.g.dart';

/// Configuration for the Praxis API connection.
@freezed
class ApiConfig with _$ApiConfig {
  const factory ApiConfig({
    required String baseUrl,
    @Default(Duration(seconds: 10)) Duration connectTimeout,
    @Default(Duration(seconds: 30)) Duration receiveTimeout,
  }) = _ApiConfig;

  factory ApiConfig.fromJson(Map<String, dynamic> json) =>
      _$ApiConfigFromJson(json);
}
