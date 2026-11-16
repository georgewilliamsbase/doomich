import 'package:doomich_api/doomich_api.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Токены в системном хранилище секретов: Android Keystore, Windows Credential Manager, libsecret на Linux.
class SecureTokenStore implements TokenStore {
  SecureTokenStore([FlutterSecureStorage? storage]) : _s = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _s;
  String? _access;
  String? _refresh;
  bool _loaded = false;

  static const _kAccess = 'doomich.access';
  static const _kRefresh = 'doomich.refresh';

  Future<void> _load() async {
    if (_loaded) return;
    _access = await _s.read(key: _kAccess);
    _refresh = await _s.read(key: _kRefresh);
    _loaded = true;
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
    await _s.write(key: _kAccess, value: access);
    await _s.write(key: _kRefresh, value: refresh);
  }

  @override
  Future<void> clear() async {
    _access = null;
    _refresh = null;
    _loaded = true;
    await _s.delete(key: _kAccess);
    await _s.delete(key: _kRefresh);
  }
}
