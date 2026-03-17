import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../../models/trust_entry.dart';

/// API endpoints for the EATP trust chain.
class TrustApi {
  final Dio _dio;

  TrustApi(this._dio);

  /// Get the trust chain for a session.
  Future<List<TrustEntry>> getChain(String sessionId) async {
    final response = await _dio.get<List<dynamic>>(
      '/sessions/$sessionId/trust-chain',
    );
    return response.data!
        .map((e) => TrustEntry.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Get details of a specific trust entry.
  Future<TrustEntry> getEntry(String id) async {
    final response =
        await _dio.get<Map<String, dynamic>>('/trust/entries/$id');
    return TrustEntry.fromJson(response.data!);
  }

  /// Verify a trust entry's cryptographic integrity.
  Future<Map<String, dynamic>> verify(String id) async {
    final response =
        await _dio.post<Map<String, dynamic>>('/trust/verify/$id');
    return response.data!;
  }

  /// Export a verification bundle for a session as a binary download.
  Future<Uint8List> exportBundle(String sessionId) async {
    final response = await _dio.get<List<int>>(
      '/sessions/$sessionId/export-bundle',
      options: Options(responseType: ResponseType.bytes),
    );
    return Uint8List.fromList(response.data!);
  }
}
