import 'dart:async';

import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:logger/logger.dart';

// Firebase imports — uncomment when firebase_core and firebase_messaging are
// configured with valid google-services.json / GoogleService-Info.plist.
// import 'package:firebase_core/firebase_core.dart';
// import 'package:firebase_messaging/firebase_messaging.dart';

/// Top-level background message handler for Firebase Cloud Messaging.
///
/// Must be a top-level function (not a class method) so the Dart isolate can
/// resolve it when the app is backgrounded or terminated.
///
/// Uncomment the @pragma annotation and FirebaseMessaging parameter when
/// Firebase dependencies are active.
// @pragma('vm:entry-point')
// Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
//   // Ensure Firebase is initialized in the background isolate.
//   await Firebase.initializeApp();
//   await PushNotificationService._handleRemoteMessage(message);
// }

/// Push notification service for the mobile app.
///
/// Provides two notification paths:
///
/// 1. **Local notifications** — always available, used for in-app alerts and
///    when Firebase is not configured. This path works out of the box.
///
/// 2. **Firebase Cloud Messaging (FCM)** — provides server-initiated push
///    notifications for held actions, constraint alerts, and session status
///    changes. Requires Firebase project configuration:
///
///    **Android**: Place `google-services.json` in `android/app/`.
///    **iOS**: Place `GoogleService-Info.plist` in `ios/Runner/`.
///
///    Then uncomment the Firebase sections in this file and add these
///    dependencies to `pubspec.yaml`:
///    ```yaml
///    firebase_core: ^3.0.0
///    firebase_messaging: ^15.0.0
///    ```
class PushNotificationService {
  static final Logger _logger = Logger();
  static final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();

  /// The current FCM token, or null if Firebase is not configured.
  static String? _fcmToken;

  /// Stream controller for FCM token refresh events.
  static final StreamController<String> _tokenRefreshController =
      StreamController<String>.broadcast();

  /// Stream of FCM token updates. Subscribe to send the token to your backend.
  static Stream<String> get onTokenRefresh => _tokenRefreshController.stream;

  /// The most recently obtained FCM token.
  static String? get fcmToken => _fcmToken;

  /// Initialize the push notification service.
  ///
  /// Call this during app startup, after WidgetsFlutterBinding.ensureInitialized().
  ///
  /// Initialization order:
  /// 1. Local notifications (always)
  /// 2. Firebase (if configured)
  /// 3. FCM token registration
  static Future<void> initialize() async {
    // ---- Step 1: Local notifications ----
    await _initializeLocalNotifications();
    await _createNotificationChannels();

    // ---- Step 2: Firebase Cloud Messaging ----
    await _initializeFirebase();

    _logger.i('Push notification service initialized');
  }

  /// Initialize the local notification plugin.
  static Future<void> _initializeLocalNotifications() async {
    const androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    const settings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _localNotifications.initialize(
      settings,
      onDidReceiveNotificationResponse: _onNotificationTap,
    );
  }

  /// Initialize Firebase and register for push notifications.
  ///
  /// This method is safe to call even when Firebase is not configured — it
  /// catches initialization errors gracefully and falls back to local-only
  /// notifications.
  static Future<void> _initializeFirebase() async {
    // TODO: Uncomment when Firebase is configured with valid project files.
    //
    // try {
    //   await Firebase.initializeApp();
    //
    //   final messaging = FirebaseMessaging.instance;
    //
    //   // Request permission (iOS requires explicit permission)
    //   final settings = await messaging.requestPermission(
    //     alert: true,
    //     badge: true,
    //     sound: true,
    //     provisional: false,
    //   );
    //
    //   if (settings.authorizationStatus == AuthorizationStatus.denied) {
    //     _logger.w('Push notification permission denied by user');
    //     return;
    //   }
    //
    //   // Register background handler
    //   FirebaseMessaging.onBackgroundMessage(
    //       _firebaseMessagingBackgroundHandler);
    //
    //   // Get initial FCM token
    //   _fcmToken = await messaging.getToken();
    //   if (_fcmToken != null) {
    //     _logger.i('FCM token obtained: ${_fcmToken!.substring(0, 12)}...');
    //     _tokenRefreshController.add(_fcmToken!);
    //   }
    //
    //   // Listen for token refresh
    //   messaging.onTokenRefresh.listen((newToken) {
    //     _fcmToken = newToken;
    //     _logger.i('FCM token refreshed');
    //     _tokenRefreshController.add(newToken);
    //   });
    //
    //   // Handle foreground messages
    //   FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    //
    //   // Handle notification tap when app is in background
    //   FirebaseMessaging.onMessageOpenedApp.listen(_handleMessageOpenedApp);
    //
    //   // Check if app was opened from a terminated state via notification
    //   final initialMessage = await messaging.getInitialMessage();
    //   if (initialMessage != null) {
    //     _handleMessageOpenedApp(initialMessage);
    //   }
    //
    // } catch (e) {
    //   _logger.w(
    //     'Firebase initialization skipped (not configured): $e\n'
    //     'Local notifications will still work.',
    //   );
    // }

    _logger.i(
      'Firebase push notifications not yet configured. '
      'Add google-services.json (Android) and GoogleService-Info.plist (iOS) '
      'then uncomment Firebase sections in push_notification_service.dart.',
    );
  }

  /// Handle a foreground FCM message by showing a local notification.
  ///
  /// Uncomment when Firebase is active:
  // static Future<void> _handleForegroundMessage(RemoteMessage message) async {
  //   await _handleRemoteMessage(message);
  // }

  /// Handle a notification tap when the app was in the background.
  ///
  /// Uncomment when Firebase is active:
  // static void _handleMessageOpenedApp(RemoteMessage message) {
  //   final route = message.data['route'] as String?;
  //   if (route != null) {
  //     _logger.d('Notification opened app with route: $route');
  //     // The app's deep link handler will process this route.
  //     // Deep linking is handled by GoRouter's redirect logic.
  //   }
  // }

  /// Process a remote message and route it to the appropriate local
  /// notification channel.
  ///
  /// Maps FCM data payloads to Praxis notification channels:
  /// - `type: held_action` -> approval_required channel
  /// - `type: constraint_alert` -> constraint_alert channel
  /// - `type: session_status` -> session_status channel
  /// - everything else -> general channel
  ///
  /// Uncomment when Firebase is active:
  // static Future<void> _handleRemoteMessage(RemoteMessage message) async {
  //   final notification = message.notification;
  //   final data = message.data;
  //
  //   final title = notification?.title ?? data['title'] as String? ?? 'Praxis';
  //   final body = notification?.body ?? data['body'] as String? ?? '';
  //   final type = data['type'] as String? ?? 'general';
  //
  //   final channelId = switch (type) {
  //     'held_action' => 'approval_required',
  //     'constraint_alert' => 'constraint_alert',
  //     'session_status' => 'session_status',
  //     _ => 'general',
  //   };
  //
  //   // Build deep link payload from message data
  //   final route = data['route'] as String?;
  //
  //   await showLocal(
  //     title: title,
  //     body: body,
  //     channelId: channelId,
  //     payload: route,
  //   );
  // }

  static void _onNotificationTap(NotificationResponse response) {
    final payload = response.payload;
    if (payload != null) {
      _logger.d('Notification tapped with payload: $payload');
      // The app's deep link handler will process this path.
      // GoRouter will navigate to the route specified in the payload.
    }
  }

  static Future<void> _createNotificationChannels() async {
    final androidPlugin =
        _localNotifications.resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>();
    if (androidPlugin == null) return;

    const channels = [
      AndroidNotificationChannel(
        'approval_required',
        'Approval Required',
        description: 'Notifications when AI actions need your approval',
        importance: Importance.high,
      ),
      AndroidNotificationChannel(
        'constraint_alert',
        'Constraint Alerts',
        description:
            'Warnings when constraints are approaching or exceeding limits',
        importance: Importance.high,
      ),
      AndroidNotificationChannel(
        'session_status',
        'Session Updates',
        description: 'Session started, paused, or ended notifications',
        importance: Importance.low,
      ),
      AndroidNotificationChannel(
        'general',
        'General',
        description: 'Other Praxis notifications',
        importance: Importance.defaultImportance,
      ),
    ];

    for (final channel in channels) {
      await androidPlugin.createNotificationChannel(channel);
    }
  }

  /// Show a local notification (for testing or when Firebase is not configured).
  static Future<void> showLocal({
    required String title,
    required String body,
    String channelId = 'general',
    String? payload,
  }) async {
    await _localNotifications.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title,
      body,
      NotificationDetails(
        android: AndroidNotificationDetails(
          channelId,
          channelId,
          importance: Importance.high,
        ),
        iOS: const DarwinNotificationDetails(),
      ),
      payload: payload,
    );
  }

  /// Register the FCM token with the Praxis backend.
  ///
  /// Call this after successful authentication to associate the device token
  /// with the current user. The backend uses this token to send targeted
  /// push notifications for held actions, constraint alerts, etc.
  ///
  /// Returns true if registration succeeded, false otherwise.
  static Future<bool> registerTokenWithBackend({
    required Future<void> Function(String token) registerFn,
  }) async {
    if (_fcmToken == null) {
      _logger.w('No FCM token available for backend registration');
      return false;
    }

    try {
      await registerFn(_fcmToken!);
      _logger.i('FCM token registered with backend');
      return true;
    } catch (e) {
      _logger.e('Failed to register FCM token with backend: $e');
      return false;
    }
  }

  /// Clean up resources.
  static void dispose() {
    _tokenRefreshController.close();
  }
}
