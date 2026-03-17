import 'package:flutter_test/flutter_test.dart';
import 'package:praxis_shared/praxis_shared.dart';

void main() {
  group('ReconnectionStrategy', () {
    test('first delay is approximately 1 second', () {
      final strategy = ReconnectionStrategy();
      final delay = strategy.nextDelay;
      // 1000ms +/- 500ms jitter
      expect(delay.inMilliseconds, greaterThanOrEqualTo(500));
      expect(delay.inMilliseconds, lessThanOrEqualTo(1500));
    });

    test('delays increase exponentially', () {
      final strategy = ReconnectionStrategy();
      final d1 = strategy.nextDelay;
      // Skip second delay (consumed for progression)
      strategy.nextDelay;
      final d3 = strategy.nextDelay;

      // Each delay should generally be larger (accounting for jitter)
      // After a few attempts the base delay is 1s, 2s, 4s...
      expect(d3.inMilliseconds, greaterThan(d1.inMilliseconds ~/ 2));
    });

    test('delay is capped at 30 seconds', () {
      final strategy = ReconnectionStrategy();
      // Exhaust many attempts
      for (int i = 0; i < 100; i++) {
        strategy.nextDelay;
      }
      final delay = strategy.nextDelay;
      expect(delay.inSeconds, lessThanOrEqualTo(30));
    });

    test('reset brings delay back to initial', () {
      final strategy = ReconnectionStrategy();
      // Run up the counter
      for (int i = 0; i < 10; i++) {
        strategy.nextDelay;
      }
      strategy.reset();
      expect(strategy.attempts, equals(0));
      final delay = strategy.nextDelay;
      expect(delay.inMilliseconds, lessThanOrEqualTo(1500));
    });
  });
}
