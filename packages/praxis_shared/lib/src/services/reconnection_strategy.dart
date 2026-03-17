import 'dart:math';

/// Exponential backoff strategy for WebSocket reconnection.
///
/// - Initial delay: 1 second
/// - Max delay: 30 seconds
/// - Multiplier: 2x
/// - Jitter: +/- 500ms random
/// - Max attempts: unlimited (keeps trying)
class ReconnectionStrategy {
  static const _initialDelay = Duration(seconds: 1);
  static const _maxDelay = Duration(seconds: 30);
  static const _multiplier = 2.0;
  static const _maxJitterMs = 500;

  final _random = Random();
  int _attempts = 0;

  /// Number of reconnection attempts so far.
  int get attempts => _attempts;

  /// Calculate the next delay with exponential backoff and jitter.
  Duration get nextDelay {
    final baseMs = _initialDelay.inMilliseconds * pow(_multiplier, _attempts);
    final jitter = _random.nextInt(_maxJitterMs * 2) - _maxJitterMs;
    final delayMs = (baseMs + jitter).toInt().clamp(0, _maxDelay.inMilliseconds);
    _attempts++;
    return Duration(milliseconds: delayMs);
  }

  /// Reset the attempt counter (call after a successful connection).
  void reset() => _attempts = 0;
}
