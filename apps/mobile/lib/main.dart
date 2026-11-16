import 'package:doomich_core/doomich_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';

Future<void> main() async {
  final overrides = await bootstrap(app: 'mobile');
  runApp(ProviderScope(overrides: overrides, child: const DoomichMobileApp()));
}
