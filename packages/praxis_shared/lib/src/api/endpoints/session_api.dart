import 'package:dio/dio.dart';

import '../../models/session.dart';
import '../../models/deliberation_record.dart';

/// API endpoints for CO session management.
class SessionApi {
  final Dio _dio;

  SessionApi(this._dio);

  /// List sessions, optionally filtered by state or workspace.
  Future<List<Session>> list({
    SessionStatus? status,
    String? workspaceId,
  }) async {
    final queryParams = <String, dynamic>{};
    if (status != null) queryParams['status'] = status.name;
    if (workspaceId != null) queryParams['workspace_id'] = workspaceId;

    final response = await _dio.get<List<dynamic>>(
      '/sessions',
      queryParameters: queryParams,
    );
    return response.data!
        .map((e) => Session.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// List only active sessions.
  Future<List<Session>> listActive() => list(status: SessionStatus.active);

  /// Get a single session by ID.
  Future<Session> get(String id) async {
    final response = await _dio.get<Map<String, dynamic>>('/sessions/$id');
    return Session.fromJson(response.data!);
  }

  /// Create a new session.
  Future<Session> create(CreateSessionRequest request) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/sessions',
      data: request.toJson(),
    );
    return Session.fromJson(response.data!);
  }

  /// Pause a session.
  Future<void> pause(String id, {String? reason}) async {
    await _dio.post<void>(
      '/sessions/$id/pause',
      data: {if (reason != null) 'reason': reason},
    );
  }

  /// Resume a paused session.
  Future<void> resume(String id) async {
    await _dio.post<void>('/sessions/$id/resume');
  }

  /// End a session.
  Future<void> end(String id, {String? summary}) async {
    await _dio.post<void>(
      '/sessions/$id/end',
      data: {if (summary != null) 'summary': summary},
    );
  }

  /// Get the deliberation timeline for a session.
  Future<List<DeliberationRecord>> timeline(String sessionId) async {
    final response = await _dio.get<List<dynamic>>(
      '/sessions/$sessionId/timeline',
    );
    return response.data!
        .map((e) => DeliberationRecord.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Record a decision within a session.
  Future<DeliberationRecord> decide(
    String sessionId,
    DecisionData data,
  ) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/sessions/$sessionId/decide',
      data: data.toJson(),
    );
    return DeliberationRecord.fromJson(response.data!);
  }

  /// Get recent activity feed for a session.
  Future<List<Map<String, dynamic>>> activity(String sessionId) async {
    final response = await _dio.get<List<dynamic>>(
      '/sessions/$sessionId/activity',
    );
    return response.data!.cast<Map<String, dynamic>>();
  }
}
