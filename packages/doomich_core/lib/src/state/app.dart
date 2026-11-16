import 'package:doomich_api/doomich_api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config.dart';
import '../db/app_db.dart';
import '../storage/secure_tokens.dart';
import '../storage/settings.dart';

/// Эти провайдеры переопределяются в main() приложения (см. bootstrap.dart).
final appConfigProvider = Provider<AppConfig>((ref) => throw UnimplementedError('appConfigProvider'));
final settingsStoreProvider = Provider<SettingsStore>((ref) => throw UnimplementedError('settingsStoreProvider'));
final tokenStoreProvider = Provider<TokenStore>((ref) => SecureTokenStore());
final dbProvider = Provider<AppDb>((ref) {
  final db = AppDb();
  ref.onDispose(db.close);
  return db;
});

class SettingsController extends Notifier<AppSettings> {
  @override
  AppSettings build() => ref.watch(settingsStoreProvider).load();

  Future<void> update(AppSettings Function(AppSettings s) change) async {
    state = change(state);
    await ref.read(settingsStoreProvider).save(state);
  }

  Future<void> setThemeMode(ThemeMode mode) => update((s) => s.copyWith(themeMode: mode));

  Future<void> setLocale(String? code) => update((s) => s.copyWith(localeCode: code));

  Future<void> reset() async {
    final keepServer = state.serverUrl;
    state = AppSettings(onboardingDone: true, serverUrl: keepServer);
    await ref.read(settingsStoreProvider).save(state);
  }
}

final settingsProvider = NotifierProvider<SettingsController, AppSettings>(SettingsController.new);

/// Событие "сессия потеряна": на него подписан контроллер входа.
final sessionLostProvider = NotifierProvider<SessionLost, int>(SessionLost.new);

class SessionLost extends Notifier<int> {
  @override
  int build() => 0;

  void fire() => state++;
}

final apiClientProvider = Provider<DoomichClient>((ref) {
  final config = ref.watch(appConfigProvider);
  final server = ref.watch(settingsProvider.select((s) => s.serverUrl)) ?? config.serverUrl;
  final client = DoomichClient(
    baseUrl: server,
    tokens: ref.watch(tokenStoreProvider),
    platform: AppConfig.platform,
  );
  client.onSignedOut = () => ref.read(sessionLostProvider.notifier).fire();
  return client;
});
