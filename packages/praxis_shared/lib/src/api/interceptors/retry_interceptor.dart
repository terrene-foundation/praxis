import 'dart:math';

import 'package:dio/dio.dart';
import 'package:logger/logger.dart';

/// Dio interceptor that retries failed requests with exponential backoff.
///
/// Only retries on network errors and 5xx server errors. Does not retry
/// on client errors (4xx) as those indicate the request itself is invalid.
class RetryInterceptor extends Interceptor {
  final int maxRetries;
  final Duration _initialDelay;
  final Logger _logger = Logger();

  RetryInterceptor({
    this.maxRetries = 3,
    Duration initialDelay = const Duration(seconds: 1),
  }) : _initialDelay = initialDelay;

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (!_shouldRetry(err)) {
      handler.next(err);
      return;
    }

    final retryCount =
        (err.requestOptions.extra['retryCount'] as int?) ?? 0;

    if (retryCount >= maxRetries) {
      handler.next(err);
      return;
    }

    final delay = _calculateDelay(retryCount);
    _logger.d('Retrying request (attempt ${retryCount + 1}/$maxRetries) '
        'after ${delay.inMilliseconds}ms');

    await Future<void>.delayed(delay);

    try {
      err.requestOptions.extra['retryCount'] = retryCount + 1;
      final dio = Dio(BaseOptions(
        baseUrl: err.requestOptions.baseUrl,
        headers: err.requestOptions.headers,
      ));
      final response = await dio.fetch(err.requestOptions);
      handler.resolve(response);
    } on DioException catch (retryError) {
      handler.next(retryError);
    }
  }

  bool _shouldRetry(DioException err) {
    // Retry on network errors
    if (err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        err.type == DioExceptionType.connectionError) {
      return true;
    }

    // Retry on 5xx server errors
    final statusCode = err.response?.statusCode;
    if (statusCode != null && statusCode >= 500) {
      return true;
    }

    return false;
  }

  Duration _calculateDelay(int attempt) {
    final baseDelay = _initialDelay.inMilliseconds * pow(2, attempt);
    final jitter = Random().nextInt(500) - 250; // +/- 250ms jitter
    final delayMs = (baseDelay + jitter).toInt().clamp(0, 30000);
    return Duration(milliseconds: delayMs);
  }
}
