/// Base class for all Praxis API exceptions.
///
/// Each exception type maps to a specific HTTP error category and provides
/// a user-friendly message suitable for display in the UI.
sealed class PraxisApiException implements Exception {
  /// A human-readable message describing the error.
  String get userMessage;
}

/// Network-level failure (no connectivity, DNS, timeout).
class NetworkException extends PraxisApiException {
  @override
  final String userMessage;
  final Object? cause;

  NetworkException({
    this.userMessage = 'Unable to connect to the server. Please check your network connection.',
    this.cause,
  });

  @override
  String toString() => 'NetworkException: $userMessage';
}

/// 401 Unauthorized -- token expired or invalid.
class UnauthorizedException extends PraxisApiException {
  @override
  final String userMessage;

  UnauthorizedException({
    this.userMessage = 'Your session has expired. Please log in again.',
  });

  @override
  String toString() => 'UnauthorizedException: $userMessage';
}

/// 403 Forbidden -- authenticated but lacking permission.
class ForbiddenException extends PraxisApiException {
  @override
  final String userMessage;

  ForbiddenException({
    this.userMessage = 'You do not have permission to perform this action.',
  });

  @override
  String toString() => 'ForbiddenException: $userMessage';
}

/// 404 Not Found.
class NotFoundException extends PraxisApiException {
  @override
  final String userMessage;

  NotFoundException({
    this.userMessage = 'The requested resource was not found.',
  });

  @override
  String toString() => 'NotFoundException: $userMessage';
}

/// 422 / 400 Validation error with field-level details.
class ValidationException extends PraxisApiException {
  @override
  final String userMessage;
  final Map<String, String>? fieldErrors;

  ValidationException({
    this.userMessage = 'Please check the form for errors.',
    this.fieldErrors,
  });

  @override
  String toString() => 'ValidationException: $userMessage';
}

/// 409 Conflict.
class ConflictException extends PraxisApiException {
  @override
  final String userMessage;

  ConflictException({
    this.userMessage = 'This action conflicts with the current state. Please refresh and try again.',
  });

  @override
  String toString() => 'ConflictException: $userMessage';
}

/// 500+ Server error.
class ServerException extends PraxisApiException {
  @override
  final String userMessage;
  final int? statusCode;

  ServerException({
    this.userMessage = 'An unexpected server error occurred. Please try again later.',
    this.statusCode,
  });

  @override
  String toString() => 'ServerException($statusCode): $userMessage';
}
