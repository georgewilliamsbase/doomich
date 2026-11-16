import 'dart:async';
import 'dart:convert';

import 'package:doomich_api/doomich_api.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../util/invite_link.dart';
import 'app.dart';

sealed class AuthState {
  const AuthState();
}

class SignedOut extends AuthState {
  const SignedOut();
}

class SignedIn extends AuthState {
  const SignedIn(this.me, {this.offline = false});
  final MeOut me;

  /// Профиль взят из кэша, сервер пока недоступен
  final bool offline;
}

/// Вход, регистрация и профиль. Последний профиль кэшируется, чтобы приложение
/// открывалось без сети (расписание и история доступны офлайн).
class AuthController extends AsyncNotifier<AuthState> {
  static const _cacheKey = 'me';

  DoomichClient get _api => ref.read(apiClientProvider);

  @override
  Future<AuthState> build() async {
    ref.listen(sessionLostProvider, (_, _) => _signedOut());
    final token = await ref.read(tokenStoreProvider).accessToken();
    if (token == null) return const SignedOut();
    try {
      final me = await _api.me();
      _cacheMe(me);
      return SignedIn(me);
    } on ApiException catch (e) {
      if (e.isUnauthorized) return const SignedOut();
      final cached = _cachedMe();
      if (cached != null) return SignedIn(cached, offline: true);
      rethrow;
    }
  }

  void _cacheMe(MeOut me) {
    final s = ref.read(settingsProvider);
    unawaited(ref.read(settingsProvider.notifier).update((x) => x.copyWith(extra: {...s.extra, _cacheKey: jsonEncode(me.toJson())})));
  }

  MeOut? _cachedMe() {
    final raw = ref.read(settingsProvider).extra[_cacheKey];
    if (raw is! String) return null;
    try {
      return MeOut.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  void _signedOut() {
    state = const AsyncData(SignedOut());
  }

  /// Проверка кода. Если код из QR указывает на другой сервер (установка у вуза), переключаемся на него.
  Future<InviteCheckOut> checkInvite(String raw) async {
    final link = InviteLink.parse(raw);
    if (link == null) throw ApiException('invite_invalid', 'не похоже на код приглашения');
    if (link.server != null) {
      await ref.read(settingsProvider.notifier).update((s) => s.copyWith(serverUrl: link.server));
    }
    return ref.read(apiClientProvider).checkInvite(link.code);
  }

  Future<RegisterOut> register({required String inviteCode, required String login, required String password,
      required String locale}) async {
    final code = InviteLink.parse(inviteCode)?.code ?? inviteCode;
    final out = await _api.register(inviteCode: code, login: login, password: password, locale: locale);
    _cacheMe(out.user);
    state = AsyncData(SignedIn(out.user));
    return out;
  }

  Future<void> login(String login, String password) async {
    final out = await _api.login(login, password);
    _cacheMe(out.user);
    state = AsyncData(SignedIn(out.user));
  }

  Future<String> recover({required String login, required String code, required String newPassword}) async {
    final out = await _api.recover(login: login, recoveryCode: code, newPassword: newPassword);
    _cacheMe(out.user);
    state = AsyncData(SignedIn(out.user));
    return out.recoveryCode;
  }

  Future<void> signedInWith(AuthOut out) async {
    _cacheMe(out.user);
    state = AsyncData(SignedIn(out.user));
  }

  Future<MeOut> refreshMe() async {
    final me = await _api.me();
    _cacheMe(me);
    state = AsyncData(SignedIn(me));
    return me;
  }

  Future<MeOut> updateMe(MePatch patch) async {
    final me = await _api.updateMe(patch);
    _cacheMe(me);
    state = AsyncData(SignedIn(me));
    return me;
  }

  Future<void> logout() async {
    await _api.logout();
    await ref.read(dbProvider).wipe();
    await ref.read(settingsProvider.notifier).reset();
    state = const AsyncData(SignedOut());
  }

  Future<void> deleteAccount(String password) async {
    await _api.deleteAccount(password);
    await ref.read(dbProvider).wipe();
    await ref.read(settingsProvider.notifier).reset();
    state = const AsyncData(SignedOut());
  }
}

final authProvider = AsyncNotifierProvider<AuthController, AuthState>(AuthController.new);

/// Текущий пользователь или null.
final meProvider = Provider<MeOut?>((ref) {
  final s = ref.watch(authProvider).value;
  return s is SignedIn ? s.me : null;
});

final tenantProvider = FutureProvider<TenantOut?>((ref) async {
  if (ref.watch(meProvider) == null) return null;
  return ref.read(apiClientProvider).tenant();
});
