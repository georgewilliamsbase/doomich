import 'dart:io';

/// Настройки сборки. Адрес сервера задаётся при сборке:
/// flutter build apk --dart-define=DOOMICH_SERVER=https://api.example.ru
class AppConfig {
  const AppConfig({
    required this.serverUrl,
    required this.app,
    required this.distribution,
    this.build = 1,
    this.version = '1.0.0',
  });

  /// Адрес Core API по умолчанию. Код приглашения может указать другой сервер (установка у вуза).
  final String serverUrl;

  /// mobile | desktop
  final String app;

  /// rustore | site | store | dev: откуда установлено приложение, от этого зависит проверка обновлений
  final String distribution;
  final int build;
  final String version;

  static const defaultServer = String.fromEnvironment('DOOMICH_SERVER', defaultValue: 'http://localhost:8000');
  static const defaultDistribution = String.fromEnvironment('DOOMICH_DISTRIBUTION', defaultValue: 'dev');

  /// Имя платформы так, как его понимает сервер.
  static String get platform {
    if (Platform.isAndroid) return 'android';
    if (Platform.isIOS) return 'ios';
    if (Platform.isWindows) return 'windows';
    if (Platform.isLinux) return 'linux';
    if (Platform.isMacOS) return 'macos';
    return 'other';
  }

  bool get isDesktop => app == 'desktop';
}
