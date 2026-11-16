import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

import 'chat_events.dart';
import 'errors.dart';
import 'models.g.dart';
import 'sse.dart';
import 'token_store.dart';

/// HTTP-клиент Core API.
///
/// Access-токен подставляется в каждый запрос. Если сервер ответил 401 с кодом
/// token_expired, клиент один раз обновляет токены (параллельные запросы ждут
/// одно и то же обновление) и повторяет запрос.
class DoomichClient {
  DoomichClient({
    required String baseUrl,
    required this.tokens,
    Dio? dio,
    this.onSignedOut,
    this.platform,
  }) : _dio = dio ?? Dio() {
    _dio.options
      ..baseUrl = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl
      ..connectTimeout = const Duration(seconds: 10)
      ..receiveTimeout = const Duration(seconds: 120)
      ..headers['Accept'] = 'application/json';
    _dio.interceptors.add(InterceptorsWrapper(onRequest: _onRequest, onError: _onError));
  }

  final Dio _dio;
  final TokenStore tokens;
  final String? platform;

  /// Вызывается, когда сессию восстановить нельзя (refresh отозван или истёк).
  void Function()? onSignedOut;

  Completer<bool>? _refreshing;

  String get baseUrl => _dio.options.baseUrl;
  Dio get dio => _dio;

  set baseUrl(String value) => _dio.options.baseUrl = value;

  static const _public = {
    '/v1/auth/register', '/v1/auth/login', '/v1/auth/refresh', '/v1/auth/recover', '/v1/auth/invite/check',
    '/v1/auth/login-check', '/v1/auth/qr/start', '/v1/auth/qr/poll', '/v1/app/latest',
  };

  Future<void> _onRequest(RequestOptions o, RequestInterceptorHandler h) async {
    if (!_public.contains(o.path) && o.headers['Authorization'] == null) {
      final token = await tokens.accessToken();
      if (token != null) o.headers['Authorization'] = 'Bearer $token';
    }
    h.next(o);
  }

  Future<void> _onError(DioException e, ErrorInterceptorHandler h) async {
    final r = e.response;
    final code = _errorCode(r?.data);
    final retried = e.requestOptions.extra['retried'] == true;
    if (r?.statusCode == 401 && code == 'token_expired' && !retried) {
      final ok = await refresh();
      if (ok) {
        final opts = e.requestOptions;
        opts.extra['retried'] = true;
        opts.headers['Authorization'] = 'Bearer ${await tokens.accessToken()}';
        try {
          return h.resolve(await _dio.fetch(opts));
        } on DioException catch (e2) {
          return h.next(e2);
        }
      }
    }
    h.next(e);
  }

  /// Обновление токенов. Возвращает false, если сессия окончательно потеряна.
  Future<bool> refresh() async {
    final pending = _refreshing;
    if (pending != null) return pending.future;
    final completer = _refreshing = Completer<bool>();
    try {
      final rt = await tokens.refreshToken();
      if (rt == null) {
        completer.complete(false);
        return false;
      }
      for (var attempt = 0; attempt < 3; attempt++) {
        try {
          final r = await _dio.post<Map<String, dynamic>>('/v1/auth/refresh', data: {'refresh_token': rt},
              options: Options(extra: {'retried': true}));
          final t = Tokens.fromJson(r.data!);
          await tokens.save(access: t.accessToken, refresh: t.refreshToken);
          completer.complete(true);
          return true;
        } on DioException catch (e) {
          final status = e.response?.statusCode;
          if (status == 409) {
            // Другой запрос уже обновил токены, ждём и пробуем прочитать новые
            await Future<void>.delayed(const Duration(milliseconds: 400));
            continue;
          }
          if (status == 401 || status == 403) {
            await tokens.clear();
            onSignedOut?.call();
            completer.complete(false);
            return false;
          }
          rethrow;
        }
      }
      completer.complete(false);
      return false;
    } catch (_) {
      if (!completer.isCompleted) completer.complete(false);
      return false;
    } finally {
      _refreshing = null;
    }
  }

  static String? _errorCode(dynamic data) {
    if (data is Map && data['error'] is Map) return (data['error'] as Map)['code'] as String?;
    return null;
  }

  static ApiException _map(Object e) {
    if (e is ApiException) return e;
    if (e is DioException) {
      final r = e.response;
      if (r == null) return ApiException.network(e.message ?? 'нет соединения');
      final data = r.data;
      if (data is Map && data['error'] is Map) {
        final err = Map<String, dynamic>.from(data['error'] as Map);
        return ApiException(err['code'] as String? ?? 'error', err['message'] as String? ?? '',
            status: r.statusCode, details: Map<String, dynamic>.from(err['details'] as Map? ?? const {}));
      }
      return ApiException('http_${r.statusCode}', r.statusMessage ?? '', status: r.statusCode);
    }
    return ApiException('internal', e.toString());
  }

  Future<T> _json<T>(Future<Response<dynamic>> Function() call, T Function(dynamic data) parse) async {
    try {
      final r = await call();
      return parse(r.data);
    } catch (e) {
      throw _map(e);
    }
  }

  Future<void> _void(Future<Response<dynamic>> Function() call) => _json(call, (_) {});

  static List<T> _list<T>(dynamic data, T Function(Map<String, dynamic>) f) =>
      (data as List<dynamic>).map((e) => f(e as Map<String, dynamic>)).toList();

  // --- Аккаунт -----------------------------------------------------------------

  Future<InviteCheckOut> checkInvite(String code) =>
      _json(() => _dio.post('/v1/auth/invite/check', data: {'code': code}), (d) => InviteCheckOut.fromJson(d));

  Future<LoginCheckOut> checkLogin(String login) =>
      _json(() => _dio.get('/v1/auth/login-check', queryParameters: {'login': login}),
          (d) => LoginCheckOut.fromJson(d));

  Future<RegisterOut> register({required String inviteCode, required String login, required String password,
      String locale = 'ru'}) async {
    final out = await _json(
        () => _dio.post('/v1/auth/register', data: {
              'invite_code': inviteCode, 'login': login, 'password': password, 'locale': locale,
              'platform': ?platform,
            }),
        (d) => RegisterOut.fromJson(d));
    await tokens.save(access: out.tokens.accessToken, refresh: out.tokens.refreshToken);
    return out;
  }

  Future<AuthOut> login(String login, String password) async {
    final out = await _json(
        () => _dio.post('/v1/auth/login', data: {'login': login, 'password': password, 'platform': ?platform}),
        (d) => AuthOut.fromJson(d));
    await tokens.save(access: out.tokens.accessToken, refresh: out.tokens.refreshToken);
    return out;
  }

  Future<RecoverOut> recover({required String login, required String recoveryCode, required String newPassword}) async {
    final out = await _json(
        () => _dio.post('/v1/auth/recover', data: {
              'login': login, 'recovery_code': recoveryCode, 'new_password': newPassword, 'platform': ?platform,
            }),
        (d) => RecoverOut.fromJson(d));
    await tokens.save(access: out.tokens.accessToken, refresh: out.tokens.refreshToken);
    return out;
  }

  Future<void> logout() async {
    final rt = await tokens.refreshToken();
    try {
      if (rt != null) await _dio.post('/v1/auth/logout', data: {'refresh_token': rt});
    } catch (_) {
      // Выходим локально даже без сети
    } finally {
      await tokens.clear();
    }
  }

  Future<MeOut> me() => _json(() => _dio.get('/v1/me'), (d) => MeOut.fromJson(d));

  Future<MeOut> updateMe(MePatch patch) => _json(() => _dio.patch('/v1/me', data: patch.toJson()), (d) => MeOut.fromJson(d));

  Future<void> changePassword(String oldPassword, String newPassword) =>
      _void(() => _dio.post('/v1/me/password', data: {'old_password': oldPassword, 'new_password': newPassword}));

  Future<String> newRecoveryCode(String password) => _json(
      () => _dio.post('/v1/me/recovery-code', data: {'password': password}),
      (d) => RecoveryCodeOut.fromJson(d).recoveryCode);

  Future<List<SessionOut>> sessions() => _json(() => _dio.get('/v1/me/sessions'), (d) => _list(d, SessionOut.fromJson));

  Future<void> endSession(String id) => _void(() => _dio.delete('/v1/me/sessions/$id'));

  Future<MeOut> roleUpgrade(String code) =>
      _json(() => _dio.post('/v1/me/role-upgrade', data: {'code': code}), (d) => MeOut.fromJson(d));

  Future<void> deleteAccount(String password) async {
    await _void(() => _dio.delete('/v1/account', data: {'password': password}));
    await tokens.clear();
  }

  Future<QrStartOut> qrStart() => _json(() => _dio.post('/v1/auth/qr/start'), (d) => QrStartOut.fromJson(d));

  Future<void> qrApprove(String token) => _void(() => _dio.post('/v1/auth/qr/approve', data: {'token': token}));

  /// null, пока телефон не подтвердил вход.
  Future<AuthOut?> qrPoll(String token) async {
    final out = await _json(() => _dio.post('/v1/auth/qr/poll', data: {'token': token}),
        (d) => d == null ? null : AuthOut.fromJson(d as Map<String, dynamic>));
    if (out != null) await tokens.save(access: out.tokens.accessToken, refresh: out.tokens.refreshToken);
    return out;
  }

  // --- Вуз и обновления ----------------------------------------------------------

  Future<TenantOut> tenant() => _json(() => _dio.get('/v1/tenant'), (d) => TenantOut.fromJson(d));

  Future<ReleaseOut?> latestRelease({required String app, required String platform, required int build,
      String channel = 'stable', String lang = 'ru'}) =>
      _json(
          () => _dio.get('/v1/app/latest', queryParameters: {
                'app': app, 'platform': platform, 'build': build, 'channel': channel, 'lang': lang,
              }),
          (d) => d == null ? null : ReleaseOut.fromJson(d as Map<String, dynamic>));

  // --- Чаты ---------------------------------------------------------------------

  Future<List<ChatOut>> chats({int limit = 50, DateTime? before}) => _json(
      () => _dio.get('/v1/chats', queryParameters: {'limit': limit, 'before': ?before?.toUtc().toIso8601String()}),
      (d) => _list(d, ChatOut.fromJson));

  Future<ChatOut> createChat({String? title, List<String> documentIds = const [], String? lectureId}) => _json(
      () => _dio.post('/v1/chats', data: ChatCreate(title: title, documentIds: documentIds, lectureId: lectureId).toJson()),
      (d) => ChatOut.fromJson(d));

  Future<ChatOut> renameChat(String id, String title) =>
      _json(() => _dio.patch('/v1/chats/$id', data: {'title': title}), (d) => ChatOut.fromJson(d));

  Future<void> deleteChat(String id) => _void(() => _dio.delete('/v1/chats/$id'));

  Future<List<MessageOut>> messages(String chatId, {int limit = 50, DateTime? before}) => _json(
      () => _dio.get('/v1/chats/$chatId/messages',
          queryParameters: {'limit': limit, 'before': ?before?.toUtc().toIso8601String()}),
      (d) => _list(d, MessageOut.fromJson));

  /// Отправка сообщения. Ответ приходит потоком событий; поток можно прервать
  /// через [cancel], сервер сохранит то, что успел сгенерировать.
  Stream<ChatEvent> sendMessage(String chatId, MessageIn body, {CancelToken? cancel}) =>
      _stream('/v1/chats/$chatId/messages', body.toJson(), cancel);

  Stream<ChatEvent> retry(String chatId, {CancelToken? cancel}) => _stream('/v1/chats/$chatId/retry', null, cancel);

  Stream<ChatEvent> sendIncognito(IncognitoIn body, {CancelToken? cancel}) =>
      _stream('/v1/chats/incognito/messages', body.toJson(), cancel);

  Stream<ChatEvent> _stream(String path, Map<String, dynamic>? body, CancelToken? cancel) async* {
    Response<ResponseBody> r;
    try {
      r = await _dio.post<ResponseBody>(path, data: body, cancelToken: cancel,
          options: Options(responseType: ResponseType.stream, headers: {'Accept': 'text/event-stream'},
              receiveTimeout: const Duration(minutes: 5)));
    } on DioException catch (e) {
      if (CancelToken.isCancel(e)) return;
      final resp = e.response;
      if (resp != null && resp.data is ResponseBody) {
        // Тело ошибки пришло потоком, собираем его
        final bytes = await (resp.data as ResponseBody).stream.fold<List<int>>([], (a, b) => a..addAll(b));
        throw _map(DioException(requestOptions: e.requestOptions, response: Response(
            requestOptions: e.requestOptions, statusCode: resp.statusCode, data: _tryJson(bytes))));
      }
      throw _map(e);
    }
    try {
      await for (final ev in parseSse(r.data!.stream)) {
        yield ChatEvent.fromSse(ev.event, ev.json);
      }
    } on DioException catch (e) {
      if (CancelToken.isCancel(e)) return;
      throw _map(e);
    }
  }

  static dynamic _tryJson(List<int> bytes) {
    try {
      return jsonDecode(utf8.decode(bytes));
    } catch (_) {
      return null;
    }
  }

  Future<void> feedback(FeedbackIn body) => _void(() => _dio.post('/v1/feedback', data: body.toJson()));

  // --- Расписание ---------------------------------------------------------------

  Future<List<GroupOut>> groups({String? query, int limit = 50}) => _json(
      () => _dio.get('/v1/groups', queryParameters: {'q': ?query, 'limit': limit}), (d) => _list(d, GroupOut.fromJson));

  Future<List<TeacherOut>> teachers(String query) =>
      _json(() => _dio.get('/v1/teachers', queryParameters: {'q': query}), (d) => _list(d, TeacherOut.fromJson));

  Future<ScheduleOut> schedule({String? groupId, String? subgroup, String? teacherKey, DateTime? from, DateTime? to}) =>
      _json(
          () => _dio.get('/v1/schedule', queryParameters: {
                'group_id': ?groupId,
                'subgroup': ?subgroup,
                'teacher_key': ?teacherKey,
                'from': ?(from == null ? null : _day(from)),
                'to': ?(to == null ? null : _day(to)),
              }),
          (d) => ScheduleOut.fromJson(d));

  Future<NowNextOut> nowNext({String? groupId, String? subgroup, String? teacherKey}) => _json(
      () => _dio.get('/v1/schedule/now',
          queryParameters: {'group_id': ?groupId, 'subgroup': ?subgroup, 'teacher_key': ?teacherKey}),
      (d) => NowNextOut.fromJson(d));

  Future<List<ChangeOut>> scheduleChanges({required DateTime since, String? groupId}) => _json(
      () => _dio.get('/v1/schedule/changes',
          queryParameters: {'since': since.toUtc().toIso8601String(), 'group_id': ?groupId}),
      (d) => _list(d, ChangeOut.fromJson));

  static String _day(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  // --- Документы ----------------------------------------------------------------

  Future<List<DocumentOut>> documents() => _json(() => _dio.get('/v1/documents'), (d) => _list(d, DocumentOut.fromJson));

  Future<DocumentOut> document(String id) => _json(() => _dio.get('/v1/documents/$id'), (d) => DocumentOut.fromJson(d));

  Future<DocumentOut> uploadDocument({required String filename, String? path, Uint8List? bytes,
      void Function(int sent, int total)? onProgress, CancelToken? cancel}) async {
    final file = path != null
        ? await MultipartFile.fromFile(path, filename: filename)
        : MultipartFile.fromBytes(bytes!, filename: filename);
    return _json(
        () => _dio.post('/v1/documents', data: FormData.fromMap({'file': file}), onSendProgress: onProgress,
            cancelToken: cancel, options: Options(receiveTimeout: const Duration(minutes: 5))),
        (d) => DocumentOut.fromJson(d));
  }

  Future<void> deleteDocument(String id) => _void(() => _dio.delete('/v1/documents/$id'));

  Future<ChunkOut> chunk(String documentId, String chunkId) =>
      _json(() => _dio.get('/v1/documents/$documentId/chunks/$chunkId'), (d) => ChunkOut.fromJson(d));

  /// Произвольный запрос к модулям следующих релизов (лекции, курсы, кампус).
  Future<dynamic> raw(String method, String path, {Object? data, Map<String, dynamic>? query, Options? options}) =>
      _json(() => _dio.request(path, data: data, queryParameters: query,
          options: (options ?? Options()).copyWith(method: method)), (d) => d);

  /// Адрес голосового канала.
  Uri voiceUri() {
    final base = Uri.parse(baseUrl);
    return base.replace(scheme: base.scheme == 'https' ? 'wss' : 'ws', path: '${base.path}/v1/voice');
  }
}
