import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:doomich_api/doomich_api.dart';
import 'package:flutter_test/flutter_test.dart';

/// Подменный транспорт dio: отвечает по таблице маршрутов.
class FakeAdapter implements HttpClientAdapter {
  FakeAdapter(this.handler);

  final FutureOr<ResponseBody> Function(RequestOptions o) handler;
  final calls = <String>[];

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    calls.add('${options.method} ${options.path} ${options.headers['Authorization'] ?? ''}');
    return handler(options);
  }

  @override
  void close({bool force = false}) {}
}

ResponseBody jsonBody(Object data, [int status = 200]) => ResponseBody.fromString(jsonEncode(data), status,
    headers: {Headers.contentTypeHeader: [Headers.jsonContentType]});

Map<String, dynamic> me() => {
      'id': 'u1', 'login': 'Енот', 'role': 'student', 'locale': 'ru', 'history_days': 90, 'is_beta': false,
      'created_on': '2026-11-16',
      'tenant': {'id': 't1', 'slug': 'demo', 'name': 'Демо', 'timezone': 'Europe/Moscow'},
      'group': {'id': 'g1', 'code': 'ИВТ-21'},
    };

Map<String, dynamic> tokens(String a, String r) =>
    {'access_token': a, 'refresh_token': r, 'token_type': 'bearer', 'expires_in': 900, 'refresh_expires_in': 1};

void main() {
  test('SSE парсится по событиям, в том числе разрезанным на куски', () async {
    const raw = 'event: meta\ndata: {"chat_id":"c1"}\n\n: ping\n\nevent: delta\ndata: {"text":"При"}\n\n'
        'event: delta\ndata: {"text":"вет"}\n\nevent: done\ndata: {"message_id":"m1"}\n\n';
    final bytes = utf8.encode(raw);
    final chunks = [bytes.sublist(0, 7), bytes.sublist(7, 40), bytes.sublist(40)];
    final events = await parseSse(Stream.fromIterable(chunks)).toList();
    expect(events.map((e) => e.event), ['meta', 'delta', 'delta', 'done']);
    final parsed = events.map((e) => ChatEvent.fromSse(e.event, e.json)).toList();
    expect(parsed.whereType<ChatDelta>().map((e) => e.text).join(), 'Привет');
    expect((parsed.last as ChatDone).messageId, 'm1');
  });

  test('модели читают и пишут JSON', () {
    final m = MeOut.fromJson(me());
    expect(m.group!.code, 'ИВТ-21');
    expect(m.createdOn, DateTime(2026, 11, 16));
    expect(m.features, isEmpty);
    final back = m.toJson();
    expect(back['created_on'], '2026-11-16');
    expect(MessageIn(text: 'привет').toJson(), containsPair('mode', 'text'));
  });

  test('аудиокадр голосового канала', () {
    final meta = <int, Map<String, dynamic>>{};
    parseVoiceMessage({'type': 'audio_meta', 'seq': 3, 'text': 'Привет.', 'duration': 1.5}, meta);
    final frame = Uint8List.fromList([0x41, 0, 0, 0, 3, 2, 1, 2, 3]);
    final a = parseAudioFrame(frame, meta)!;
    expect(a.seq, 3);
    expect(a.format, 'ogg_opus');
    expect(a.text, 'Привет.');
    expect(a.bytes, [1, 2, 3]);
    expect(meta, isEmpty);
  });

  test('истёкший токен обновляется один раз для параллельных запросов', () async {
    final store = MemoryTokenStore();
    await store.save(access: 'old', refresh: 'r1');
    var refreshes = 0;
    final adapter = FakeAdapter((o) async {
      if (o.path == '/v1/auth/refresh') {
        refreshes++;
        await Future<void>.delayed(const Duration(milliseconds: 20));
        return jsonBody(tokens('new', 'r2'));
      }
      if (o.headers['Authorization'] == 'Bearer old') {
        return jsonBody({'error': {'code': 'token_expired', 'message': 'expired'}}, 401);
      }
      return jsonBody(me());
    });
    final dio = Dio()..httpClientAdapter = adapter;
    final client = DoomichClient(baseUrl: 'http://test', tokens: store, dio: dio);
    final results = await Future.wait([client.me(), client.me(), client.me()]);
    expect(results.every((m) => m.login == 'Енот'), isTrue);
    expect(refreshes, 1);
    expect(await store.refreshToken(), 'r2');
  });

  test('отозванная сессия выходит из аккаунта', () async {
    final store = MemoryTokenStore();
    await store.save(access: 'old', refresh: 'r1');
    var signedOut = false;
    final adapter = FakeAdapter((o) {
      if (o.path == '/v1/auth/refresh') {
        return jsonBody({'error': {'code': 'refresh_reused', 'message': ''}}, 401);
      }
      return jsonBody({'error': {'code': 'token_expired', 'message': ''}}, 401);
    });
    final client = DoomichClient(baseUrl: 'http://test', tokens: store, dio: Dio()..httpClientAdapter = adapter,
        onSignedOut: () => signedOut = true);
    await expectLater(client.me(), throwsA(isA<ApiException>().having((e) => e.status, 'status', 401)));
    expect(signedOut, isTrue);
    expect(await store.accessToken(), isNull);
  });

  test('ошибки API превращаются в ApiException с кодом', () async {
    final adapter = FakeAdapter((o) => jsonBody({'error': {'code': 'invite_invalid', 'message': 'нет такого'}}, 404));
    final client = DoomichClient(baseUrl: 'http://test', tokens: MemoryTokenStore(),
        dio: Dio()..httpClientAdapter = adapter);
    await expectLater(client.checkInvite('ABCD-EFGH'),
        throwsA(isA<ApiException>().having((e) => e.code, 'code', 'invite_invalid')));
  });

  test('ответ чата идёт потоком', () async {
    final adapter = FakeAdapter((o) => ResponseBody(
        Stream.fromIterable([utf8.encode('event: delta\ndata: {"text":"Да"}\n\n'),
          utf8.encode('event: done\ndata: {}\n\n')]), 200,
        headers: {Headers.contentTypeHeader: ['text/event-stream']}));
    final store = MemoryTokenStore();
    await store.save(access: 'a', refresh: 'r');
    final client = DoomichClient(baseUrl: 'http://test', tokens: store, dio: Dio()..httpClientAdapter = adapter);
    final events = await client.sendMessage('c1', MessageIn(text: 'ок?')).toList();
    expect(events.first, isA<ChatDelta>());
    expect(adapter.calls.single, 'POST /v1/chats/c1/messages Bearer a');
    expect(client.voiceUri().toString(), 'ws://test/v1/voice');
  });
}
