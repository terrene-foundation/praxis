import 'package:dio/dio.dart';

import '../../models/constraint_set.dart';

/// API endpoints for constraint management.
class ConstraintApi {
  final Dio _dio;

  ConstraintApi(this._dio);

  /// Get the current constraints for a session.
  Future<ConstraintSet> get(String sessionId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/sessions/$sessionId/constraints',
    );
    return ConstraintSet.fromJson(response.data!);
  }

  /// Update the constraints for a session.
  Future<ConstraintSet> update(
    String sessionId,
    ConstraintSet constraints,
  ) async {
    final response = await _dio.put<Map<String, dynamic>>(
      '/sessions/$sessionId/constraints',
      data: constraints.toJson(),
    );
    return ConstraintSet.fromJson(response.data!);
  }

  /// List available constraint presets.
  Future<List<ConstraintPreset>> listPresets() async {
    final response = await _dio.get<List<dynamic>>(
      '/constraints/presets',
    );
    return response.data!
        .map((e) => ConstraintPreset.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Get a specific constraint preset.
  Future<ConstraintPreset> getPreset(String id) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/constraints/presets/$id',
    );
    return ConstraintPreset.fromJson(response.data!);
  }
}
