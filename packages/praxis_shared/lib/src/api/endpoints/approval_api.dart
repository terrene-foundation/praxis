import 'package:dio/dio.dart';

import '../../models/held_action.dart';

/// API endpoints for the held-action approval workflow.
///
/// Held actions are scoped to sessions. The backend routes are:
/// - `GET  /sessions/{sessionId}/held-actions` — list held actions
/// - `POST /sessions/{sessionId}/approve/{heldId}` — approve
/// - `POST /sessions/{sessionId}/deny/{heldId}` — deny
class ApprovalApi {
  final Dio _dio;

  ApprovalApi(this._dio);

  /// List held actions for a session.
  Future<List<HeldAction>> listForSession(String sessionId) async {
    final response = await _dio.get<List<dynamic>>(
      '/sessions/$sessionId/held-actions',
    );
    return response.data!
        .map((e) => HeldAction.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// List all pending held actions (convenience — queries all active sessions).
  ///
  /// This is a client-side aggregation. The backend does not have a global
  /// pending-approvals endpoint; held actions are per-session.
  Future<List<HeldAction>> listPending() async {
    // Fetch active sessions and aggregate their held actions.
    final sessionsResponse = await _dio.get<List<dynamic>>('/sessions');
    final sessions = sessionsResponse.data ?? [];
    final allHeld = <HeldAction>[];
    for (final s in sessions) {
      final sessionMap = s as Map<String, dynamic>;
      final sessionId = sessionMap['id'] as String;
      try {
        final response = await _dio.get<List<dynamic>>(
          '/sessions/$sessionId/held-actions',
        );
        allHeld.addAll(
          (response.data ?? [])
              .map((e) => HeldAction.fromJson(e as Map<String, dynamic>)),
        );
      } catch (_) {
        // Session may have ended between listing and fetching; skip.
      }
    }
    return allHeld;
  }

  /// Approve a held action within a session.
  Future<void> approve(String sessionId, String heldId) async {
    await _dio.post<void>('/sessions/$sessionId/approve/$heldId');
  }

  /// Deny a held action within a session.
  Future<void> deny(String sessionId, String heldId) async {
    await _dio.post<void>('/sessions/$sessionId/deny/$heldId');
  }

  /// Approve a held action with conditions attached.
  Future<void> approveWithConditions(
    String sessionId,
    String heldId,
    String conditions,
  ) async {
    await _dio.post<void>(
      '/sessions/$sessionId/approve/$heldId',
      data: {'conditions': conditions},
    );
  }
}
