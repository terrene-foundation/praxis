import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:praxis_shared/praxis_shared.dart';

import 'app.dart';
import 'core/providers/app_providers.dart';
import 'core/services/push_notification_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize push notification service (local notifications).
  // Firebase initialization would go here once google-services.json /
  // GoogleService-Info.plist are configured.
  await PushNotificationService.initialize();

  runApp(
    ProviderScope(
      overrides: mobileProviderOverrides(),
      child: const _AppInitializer(),
    ),
  );
}

/// Restores the auth session on startup, then renders the app.
class _AppInitializer extends ConsumerStatefulWidget {
  const _AppInitializer();

  @override
  ConsumerState<_AppInitializer> createState() => _AppInitializerState();
}

class _AppInitializerState extends ConsumerState<_AppInitializer> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      ref.read(authNotifierProvider.notifier).restoreSession();
    });
  }

  @override
  Widget build(BuildContext context) {
    return const PraxisMobileApp();
  }
}
