import 'package:doomich_core/doomich_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hotkey_manager/hotkey_manager.dart';
import 'package:window_manager/window_manager.dart';

import 'app.dart';

Future<void> main() async {
  final overrides = await bootstrap(app: 'desktop');
  await hotKeyManager.unregisterAll();
  final window = WindowManager.instance.getCurrent();
  if (window != null) {
    window.title = 'Думыч';
    window.setSize(const Size(1200, 800).toNative(), false);
    window.minimumSize = const Size(880, 600).toNative();
    window.center();
    window.show();
  }
  runApp(ProviderScope(overrides: overrides, child: const DoomichDesktopApp()));
}
