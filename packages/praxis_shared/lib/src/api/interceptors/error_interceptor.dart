import 'package:dio/dio.dart';

import '../praxis_api_exception.dart';

/// Dio interceptor that maps HTTP errors to typed [PraxisApiException] subclasses.
class ErrorInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final PraxisApiException mappedException;

    if (err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        err.type == DioExceptionType.connectionError) {
      mappedException = NetworkException(cause: err);
    } else if (err.response == null) {
      mappedException = NetworkException(cause: err);
    } else {
      final statusCode = err.response!.statusCode;
      final body = err.response!.data;
      final serverMessage = _extractMessage(body);

      switch (statusCode) {
        case 401:
          mappedException = UnauthorizedException(
            userMessage: serverMessage ?? 'Your session has expired. Please log in again.',
          );
        case 403:
          mappedException = ForbiddenException(
            userMessage: serverMessage ?? 'You do not have permission to perform this action.',
          );
        case 404:
          mappedException = NotFoundException(
            userMessage: serverMessage ?? 'The requested resource was not found.',
          );
        case 409:
          mappedException = ConflictException(
            userMessage: serverMessage ?? 'This action conflicts with the current state.',
          );
        case 400 || 422:
          final fieldErrors = _extractFieldErrors(body);
          mappedException = ValidationException(
            userMessage: serverMessage ?? 'Please check the form for errors.',
            fieldErrors: fieldErrors,
          );
        default:
          if (statusCode != null && statusCode >= 500) {
            mappedException = ServerException(
              userMessage: serverMessage ?? 'An unexpected server error occurred.',
              statusCode: statusCode,
            );
          } else {
            mappedException = ServerException(
              userMessage: serverMessage ?? 'An unexpected error occurred.',
              statusCode: statusCode,
            );
          }
      }
    }

    handler.reject(
      DioException(
        requestOptions: err.requestOptions,
        response: err.response,
        type: err.type,
        error: mappedException,
      ),
    );
  }

  String? _extractMessage(dynamic body) {
    if (body is Map<String, dynamic>) {
      return body['message'] as String? ??
          body['detail'] as String? ??
          body['error'] as String?;
    }
    return null;
  }

  Map<String, String>? _extractFieldErrors(dynamic body) {
    if (body is Map<String, dynamic> && body.containsKey('errors')) {
      final errors = body['errors'];
      if (errors is Map<String, dynamic>) {
        return errors.map((key, value) => MapEntry(key, value.toString()));
      }
    }
    return null;
  }
}
