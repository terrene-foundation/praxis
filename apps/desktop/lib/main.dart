import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:marionette_flutter/marionette_flutter.dart';
import 'package:praxis_shared/praxis_shared.dart';
import 'package:window_manager/window_manager.dart';

import 'app.dart';
import 'core/providers/app_providers.dart';
import 'services/tray_service.dart';

void main() async {
  // Initialize Marionette binding for debug-mode UI testing, falls back to
  // standard Flutter binding in release builds.
  if (kDebugMode) {
    MarionetteBinding.ensureInitialized();
  } else {
    WidgetsFlutterBinding.ensureInitialized();
  }

  // Desktop window configuration
  await windowManager.ensureInitialized();
  const windowOptions = WindowOptions(
    size: Size(1280, 800),
    minimumSize: Size(900, 600),
    center: true,
    title: 'Praxis',
    titleBarStyle: TitleBarStyle.normal,
  );
  windowManager.waitUntilReadyToShow(windowOptions, () async {
    await windowManager.show();
    await windowManager.focus();
  });

  // Initialize system tray
  final trayService = TrayService();
  try {
    await trayService.init();
  } catch (_) {
    // System tray may not be available on all platforms (e.g. Wayland
    // without a tray host). Continue without it.
  }

  runApp(
    ProviderScope(
      overrides: desktopProviderOverrides(),
      child: _AppInitializer(trayService: trayService),
    ),
  );
}

/// Restores the auth session on startup, then renders the app.
///
/// Also listens for window close events to minimize to tray instead of
/// quitting, and keeps the tray menu counts up to date.
class _AppInitializer extends ConsumerStatefulWidget {
  final TrayService trayService;

  const _AppInitializer({required this.trayService});

  @override
  ConsumerState<_AppInitializer> createState() => _AppInitializerState();
}

class _AppInitializerState extends ConsumerState<_AppInitializer>
    with WindowListener {
  @override
  void initState() {
    super.initState();
    windowManager.addListener(this);
    // Prevent the default close behavior so we can minimize to tray.
    windowManager.setPreventClose(true);

    // Attempt to restore a previous session from stored tokens.
    Future.microtask(() {
      ref.read(authNotifierProvider.notifier).restoreSession();
    });
  }

  @override
  void dispose() {
    windowManager.removeListener(this);
    widget.trayService.dispose();
    super.dispose();
  }

  @override
  void onWindowClose() async {
    // Minimize to tray instead of quitting.
    await widget.trayService.hideWindow();
  }

  @override
  Widget build(BuildContext context) {
    // Keep tray counts updated whenever sessions or approvals change.
    ref.listen(activeSessionsProvider, (_, next) {
      final count = next.maybeWhen(data: (l) => l.length, orElse: () => 0);
      widget.trayService.updateCounts(
        activeSessions: count,
        pendingApprovals:
            ref.read(pendingApprovalCountProvider),
      );
    });
    ref.listen(pendingApprovalsProvider, (_, next) {
      final count = next.maybeWhen(data: (l) => l.length, orElse: () => 0);
      widget.trayService.updateCounts(
        activeSessions: ref
            .read(activeSessionsProvider)
            .maybeWhen(data: (l) => l.length, orElse: () => 0),
        pendingApprovals: count,
      );
    });

    return const PraxisDesktopApp();
  }
}
