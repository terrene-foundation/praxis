import 'package:tray_manager/tray_manager.dart';
import 'package:window_manager/window_manager.dart';

/// Manages the system tray icon, context menu, and window show/hide behavior.
///
/// Uses [tray_manager] to display a tray icon with a context menu showing
/// live counts of active sessions and pending approvals. Clicking the tray
/// icon toggles window visibility.
class TrayService with TrayListener {
  int _activeSessions = 0;
  int _pendingApprovals = 0;

  /// Initialize the system tray icon and menu.
  ///
  /// The [tray_manager] package reads icon paths relative to the Flutter
  /// assets directory bundled into the executable. We pass the Flutter
  /// asset path directly.
  Future<void> init() async {
    await trayManager.setIcon('assets/tray_icon.png');
    await trayManager.setToolTip('Praxis - CO Collaboration Platform');
    trayManager.addListener(this);
    await _rebuildMenu();
  }

  /// Update the session and approval counts displayed in the tray menu.
  Future<void> updateCounts({
    required int activeSessions,
    required int pendingApprovals,
  }) async {
    _activeSessions = activeSessions;
    _pendingApprovals = pendingApprovals;
    await _rebuildMenu();
  }

  /// Show the main application window and bring it to front.
  Future<void> showWindow() async {
    await windowManager.show();
    await windowManager.focus();
  }

  /// Hide the application window (minimize to tray).
  Future<void> hideWindow() async {
    await windowManager.hide();
  }

  // -- TrayListener overrides ------------------------------------------------

  @override
  void onTrayIconMouseDown() {
    _toggleWindow();
  }

  @override
  void onTrayIconRightMouseDown() {
    trayManager.popUpContextMenu();
  }

  @override
  void onTrayMenuItemClick(MenuItem menuItem) {
    switch (menuItem.key) {
      case 'show_dashboard':
        showWindow();
      case 'quit':
        windowManager.destroy();
    }
  }

  // -- Private helpers -------------------------------------------------------

  Future<void> _toggleWindow() async {
    final isVisible = await windowManager.isVisible();
    if (isVisible) {
      await hideWindow();
    } else {
      await showWindow();
    }
  }

  Future<void> _rebuildMenu() async {
    final menu = Menu(
      items: [
        MenuItem(
          key: 'show_dashboard',
          label: 'Show Dashboard',
        ),
        MenuItem.separator(),
        MenuItem(
          label: 'Active Sessions: $_activeSessions',
          disabled: true,
        ),
        MenuItem(
          label: 'Pending Approvals: $_pendingApprovals',
          disabled: true,
        ),
        MenuItem.separator(),
        MenuItem(
          key: 'quit',
          label: 'Quit',
        ),
      ],
    );
    await trayManager.setContextMenu(menu);
  }

  /// Clean up tray resources.
  Future<void> dispose() async {
    trayManager.removeListener(this);
    await trayManager.destroy();
  }
}
