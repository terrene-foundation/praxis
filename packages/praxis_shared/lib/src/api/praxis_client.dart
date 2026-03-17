import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../auth/token_provider.dart';
import 'endpoints/approval_api.dart';
import 'endpoints/auth_api.dart';
import 'endpoints/constraint_api.dart';
import 'endpoints/delegation_api.dart';
import 'endpoints/session_api.dart';
import 'endpoints/trust_api.dart';
import 'interceptors/auth_interceptor.dart';
import 'interceptors/error_interceptor.dart';
import 'interceptors/retry_interceptor.dart';

/// Typed REST API client for all Praxis backend endpoints.
///
/// Organizes endpoints into logical groups (sessions, constraints, approvals,
/// trust, delegations, auth) and wires up authentication, error mapping, and
/// retry interceptors automatically.
class PraxisClient {
  final Dio _dio;

  /// Session management endpoints.
  late final SessionApi sessions;

  /// Constraint management endpoints.
  late final ConstraintApi constraints;

  /// Held-action approval endpoints.
  late final ApprovalApi approvals;

  /// EATP trust chain endpoints.
  late final TrustApi trust;

  /// Delegation management endpoints.
  late final DelegationApi delegations;

  /// Authentication endpoints.
  late final AuthApi auth;

  PraxisClient({
    required String baseUrl,
    required TokenProvider tokenProvider,
    Duration connectTimeout = const Duration(seconds: 10),
    Duration receiveTimeout = const Duration(seconds: 30),
  }) : _dio = Dio(BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: connectTimeout,
          receiveTimeout: receiveTimeout,
          headers: {'Content-Type': 'application/json'},
        )) {
    _dio.interceptors.addAll([
      AuthInterceptor(tokenProvider),
      RetryInterceptor(maxRetries: 3),
      ErrorInterceptor(),
      if (kDebugMode)
        LogInterceptor(requestBody: true, responseBody: true),
    ]);

    sessions = SessionApi(_dio);
    constraints = ConstraintApi(_dio);
    approvals = ApprovalApi(_dio);
    trust = TrustApi(_dio);
    delegations = DelegationApi(_dio);
    auth = AuthApi(_dio);
  }

  /// The underlying Dio instance, exposed for advanced use cases.
  Dio get dio => _dio;
}
