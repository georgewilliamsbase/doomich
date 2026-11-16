import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/misc.dart' show Override;
import 'package:package_info_plus/package_info_plus.dart';

import 'config.dart';
import 'state/app.dart';
import 'storage/settings.dart';

/// Общая инициализация обоих приложений: настройки, версия, адрес сервера.
Future<List<Override>> bootstrap({required String app}) async {
  WidgetsFlutterBinding.ensureInitialized();
  final store = await SettingsStore.open();
  var version = '1.0.0';
  var build = 1;
  try {
    final info = await PackageInfo.fromPlatform();
    version = info.version;
    build = int.tryParse(info.buildNumber) ?? 1;
  } catch (_) {
    // В тестах плагина нет
  }
  final config = AppConfig(
    serverUrl: AppConfig.defaultServer,
    app: app,
    distribution: AppConfig.defaultDistribution,
    build: build,
    version: version,
  );
  return [
    appConfigProvider.overrideWithValue(config),
    settingsStoreProvider.overrideWithValue(store),
  ];
}
