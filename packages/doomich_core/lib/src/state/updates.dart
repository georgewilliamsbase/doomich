import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:doomich_api/doomich_api.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';

import '../config.dart';
import 'app.dart';

/// Проверка обновлений для сборок вне магазинов (APK с сайта, Windows, Linux).
/// RuStore обновляет приложение сам, там проверка не нужна.
final updateProvider = FutureProvider<ReleaseOut?>((ref) async {
  final config = ref.watch(appConfigProvider);
  if (config.distribution == 'rustore' || config.distribution == 'store') return null;
  final platform = switch (AppConfig.platform) {
    'linux' => const String.fromEnvironment('DOOMICH_LINUX_PACKAGE', defaultValue: 'linux-appimage'),
    final p => p,
  };
  try {
    return await ref.read(apiClientProvider).latestRelease(app: config.app, platform: platform, build: config.build,
        channel: const String.fromEnvironment('DOOMICH_CHANNEL', defaultValue: 'stable'));
  } on ApiException {
    return null;
  }
});

/// Скачивает пакет обновления и проверяет SHA-256. Возвращает путь к файлу.
Future<File> downloadUpdate(DoomichClient api, ReleaseOut release, {void Function(double)? onProgress}) async {
  final dir = await getTemporaryDirectory();
  final name = Uri.parse(release.url).pathSegments.last;
  final file = File('${dir.path}/$name');
  await api.dio.download(release.url, file.path, onReceiveProgress: (r, t) {
    if (t > 0) onProgress?.call(r / t);
  });
  final digest = sha256.convert(await file.readAsBytes()).toString();
  if (digest != release.sha256) {
    await file.delete();
    throw ApiException('update_checksum', 'контрольная сумма не совпала');
  }
  return file;
}

String describeRelease(ReleaseOut r) => jsonEncode(r.toJson());
