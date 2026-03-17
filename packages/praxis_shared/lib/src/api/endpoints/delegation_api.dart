import 'package:dio/dio.dart';

import '../../models/delegation.dart';
import '../../models/constraint_set.dart';

/// API endpoints for delegation management.
class DelegationApi {
  final Dio _dio;

  DelegationApi(this._dio);

  /// List all delegations.
  Future<List<Delegation>> list() async {
    final response = await _dio.get<List<dynamic>>('/delegations');
    return response.data!
        .map((e) => Delegation.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Create a new delegation.
  Future<Delegation> create({
    required String delegateeId,
    required ConstraintSet constraints,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/delegations',
      data: {
        'delegatee_id': delegateeId,
        'constraints': constraints.toJson(),
      },
    );
    return Delegation.fromJson(response.data!);
  }

  /// Revoke a delegation.
  Future<void> revoke(String id) async {
    await _dio.delete<void>('/delegations/$id');
  }

  /// Tighten the constraints on a delegation (can only narrow, never widen).
  Future<Delegation> tightenConstraints(
    String id,
    ConstraintSet constraints,
  ) async {
    final response = await _dio.put<Map<String, dynamic>>(
      '/delegations/$id/constraints',
      data: constraints.toJson(),
    );
    return Delegation.fromJson(response.data!);
  }
}
