import 'dart:convert';
import 'dart:io';

import 'package:doomich_api/doomich_api.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:path_provider/path_provider.dart';

/// Токены в системном хранилище секретов: Android Keystore, Windows Credential Manager, libsecret на Linux.
///
/// На некоторых сборках Linux (минимальные окружения, часть российских дистрибутивов) службы
/// секретов нет. Тогда токены пишутся в файл в каталоге приложения с правами 0600,
/// чтобы вход не ломался. Это слабее хранилища секретов, поэтому в журнал пишется предупреждение.
class SecureTokenStore implements TokenStore {
  SecureTokenStore([FlutterSecureStorage? storage, this._fallbackDir])
      : _s = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _s;
  final Directory? _fallbackDir;
  String? _access;
  String? _refresh;
  bool _loaded = false;
  bool _useFile = false;

  static const _kAccess = 'doomich.access';
  static const _kRefresh = 'doomich.refresh';

  Future<File> _file() async {
    final dir = _fallbackDir ?? await getApplicationSupportDirectory();
    await dir.create(recursive: true);
    return File('${dir.path}/tokens.json');
  }

  Future<void> _load() async {
    if (_loaded) return;
    try {
      _access = await _s.read(key: _kAccess);
      _refresh = await _s.read(key: _kRefresh);
    } catch (e) {
      _switchToFile(e);
    }
    if (_useFile || (_access == null && _refresh == null)) {
      final f = await _file();
      if (await f.exists()) {
        try {
          final j = jsonDecode(await f.readAsString()) as Map<String, dynamic>;
          _access = j['access'] as String?;
          _refresh = j['refresh'] as String?;
          _useFile = true;
        } catch (_) {
          await f.delete();
        }
      }
    }
    _loaded = true;
  }

  void _switchToFile(Object error) {
    if (!_useFile) {
      debugPrint('Хранилище секретов недоступно ($error), токены сохраняются в файл приложения');
    }
    _useFile = true;
  }

  Future<void> _writeFile() async {
    final f = await _file();
    await f.writeAsString(jsonEncode({'access': _access, 'refresh': _refresh}), flush: true);
    if (!Platform.isWindows) {
      await Process.run('chmod', ['600', f.path]);
    }
  }

  @override
  Future<String?> accessToken() async {
    await _load();
    return _access;
  }

  @override
  Future<String?> refreshToken() async {
    await _load();
    return _refresh;
  }

  @override
  Future<void> save({required String access, required String refresh}) async {
    _access = access;
    _refresh = refresh;
    _loaded = true;
    if (!_useFile) {
      try {
        await _s.write(key: _kAccess, value: access).timeout(const Duration(seconds: 5));
        await _s.write(key: _kRefresh, value: refresh).timeout(const Duration(seconds: 5));
        return;
      } catch (e) {
        _switchToFile(e);
      }
    }
    await _writeFile();
  }

  @override
  Future<void> clear() async {
    _access = null;
    _refresh = null;
    _loaded = true;
    try {
      await _s.delete(key: _kAccess);
      await _s.delete(key: _kRefresh);
    } catch (_) {}
    final f = await _file();
    if (await f.exists()) await f.delete();
  }
}
