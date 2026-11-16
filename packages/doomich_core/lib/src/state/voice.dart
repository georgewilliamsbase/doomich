import 'dart:async';
import 'dart:io';
import 'dart:typed_data';

import 'package:doomich_api/doomich_api.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../voice/audio_io.dart';
import 'app.dart';
import 'chats.dart';

enum VoicePhase { idle, connecting, listening, thinking, speaking }

class VoiceState {
  const VoiceState({this.phase = VoicePhase.idle, this.transcript = '', this.answer = '', this.level = 0, this.error,
      this.tool, this.sources = const [], this.timings = const {}});

  final VoicePhase phase;
  final String transcript;
  final String answer;
  final double level;
  final String? error;
  final String? tool;
  final List<Source> sources;
  final Map<String, double> timings;

  bool get busy => phase != VoicePhase.idle;

  VoiceState copyWith({VoicePhase? phase, String? transcript, String? answer, double? level, Object? error = _k,
      Object? tool = _k, List<Source>? sources, Map<String, double>? timings}) =>
      VoiceState(
        phase: phase ?? this.phase,
        transcript: transcript ?? this.transcript,
        answer: answer ?? this.answer,
        level: level ?? this.level,
        error: identical(error, _k) ? this.error : error as String?,
        tool: identical(tool, _k) ? this.tool : tool as String?,
        sources: sources ?? this.sources,
        timings: timings ?? this.timings,
      );
}

const _k = Object();

/// Голосовой режим "нажми и говори".
///
/// listen() открывает соединение (если его нет), включает микрофон и шлёт start;
/// send() останавливает запись и шлёт end; cancel() отменяет запись или ответ.
/// Звук пользователя уходит на сервер кусками по ~100 мс и нигде не сохраняется.
class VoiceController extends Notifier<VoiceState> {
  VoiceConnection? _conn;
  StreamSubscription<VoiceEvent>? _sub;
  StreamSubscription<double>? _levelSub;
  MicRecorder? _mic;
  SpeechQueue? _player;
  String? _chatId;
  final _vad = EnergyVad();
  bool autoStop = false;

  @override
  VoiceState build() {
    ref.onDispose(_dispose);
    return const VoiceState();
  }

  MicRecorder get _recorder => _mic ??= MicRecorder();
  SpeechQueue get _queue {
    final q = _player ??= SpeechQueue();
    return q;
  }

  /// Форматы, которые точно играют системные декодеры платформы.
  List<String> get _formats => Platform.isLinux ? const ['ogg_opus', 'wav'] : const ['wav'];

  Future<VoiceConnection> _connection() async {
    final existing = _conn;
    if (existing != null) return existing;
    final api = ref.read(apiClientProvider);
    var token = await ref.read(tokenStoreProvider).accessToken();
    if (token == null) throw ApiException('unauthorized', 'нет токена', status: 401);
    VoiceConnection conn;
    try {
      conn = await VoiceConnection.connect(api.voiceUri(), token);
    } catch (_) {
      // Токен мог истечь: обновляем и пробуем ещё раз
      if (!await api.refresh()) rethrow;
      token = await ref.read(tokenStoreProvider).accessToken();
      conn = await VoiceConnection.connect(api.voiceUri(), token!);
    }
    _conn = conn;
    _sub = conn.events.listen(_onEvent, onDone: () {
      _conn = null;
      if (state.phase != VoicePhase.idle) state = state.copyWith(phase: VoicePhase.idle, error: 'network');
    }, onError: (_) {
      _conn = null;
      state = state.copyWith(phase: VoicePhase.idle, error: 'network');
    });
    return conn;
  }

  Future<bool> hasPermission() => _recorder.hasPermission();

  Future<void> listen({String? chatId, String lang = 'auto'}) async {
    if (state.phase == VoicePhase.listening) return;
    await _queue.stop();
    _chatId = chatId;
    state = const VoiceState(phase: VoicePhase.connecting);
    try {
      if (!await _recorder.hasPermission()) {
        state = const VoiceState(error: 'mic_permission');
        return;
      }
      final conn = await _connection();
      final s = ref.read(settingsProvider);
      conn.start(VoiceStart(lang: lang, chatId: chatId, tts: true, speed: s.speechRate, voice: s.voice,
          context: ref.read(assistantContextProvider), formats: _formats));
      _vad.reset();
      await _recorder.start((chunk) {
        _conn?.audio(chunk);
        if (autoStop && _vad.feed(chunk)) unawaited(send());
      });
      _levelSub = _recorder.level.listen((v) => state = state.copyWith(level: v));
      state = state.copyWith(phase: VoicePhase.listening);
    } catch (e) {
      await _recorder.stop();
      state = VoiceState(error: e is ApiException ? e.code : 'network');
    }
  }

  /// Отпустили кнопку: отправляем запись.
  Future<void> send() async {
    if (state.phase != VoicePhase.listening) return;
    await _levelSub?.cancel();
    await _recorder.stop();
    _conn?.end();
    state = state.copyWith(phase: VoicePhase.thinking, level: 0);
  }

  /// Вопрос, набранный текстом, но с озвучкой ответа.
  Future<void> ask(String text, {String? chatId}) async {
    await _queue.stop();
    _chatId = chatId;
    state = VoiceState(phase: VoicePhase.thinking, transcript: text);
    try {
      final conn = await _connection();
      final s = ref.read(settingsProvider);
      conn.start(VoiceStart(text: text, chatId: chatId, speed: s.speechRate, voice: s.voice,
          context: ref.read(assistantContextProvider), formats: _formats));
    } catch (e) {
      state = VoiceState(error: e is ApiException ? e.code : 'network');
    }
  }

  /// Отмена записи, ответа или озвучки.
  Future<void> cancel() async {
    await _levelSub?.cancel();
    await _recorder.stop();
    await _queue.stop();
    _conn?.cancel();
    state = const VoiceState();
  }

  Future<void> stopSpeaking() async {
    await _queue.stop();
    if (state.phase == VoicePhase.speaking) state = state.copyWith(phase: VoicePhase.idle);
  }

  void _onEvent(VoiceEvent ev) {
    switch (ev) {
      case VoiceReady():
        break;
      case VoiceTranscript(:final text):
        state = state.copyWith(transcript: text, phase: VoicePhase.thinking);
      case VoiceAnswerDelta(:final text):
        state = state.copyWith(answer: state.answer + text);
      case VoiceTool(:final name, :final status):
        state = state.copyWith(tool: status == 'start' ? name : null);
      case VoiceAudio(:final bytes, :final format):
        state = state.copyWith(phase: VoicePhase.speaking);
        unawaited(_queue.enqueue(Uint8List.fromList(bytes), format));
      case VoiceSources(:final items):
        state = state.copyWith(sources: items);
      case VoiceDone(:final text, :final messageId, :final timings):
        state = state.copyWith(answer: text.isEmpty ? state.answer : text, timings: timings, tool: null);
        _appendToChat(messageId, text.isEmpty ? state.answer : text);
        if (!_queue.isPlaying) state = state.copyWith(phase: VoicePhase.idle);
        _queue.idle.first.then((_) {
          if (state.phase == VoicePhase.speaking) state = state.copyWith(phase: VoicePhase.idle);
        });
      case VoiceError(:final code):
        unawaited(_recorder.stop());
        state = state.copyWith(phase: VoicePhase.idle, error: code, level: 0);
      case VoiceCancelled():
        break;
    }
  }

  void _appendToChat(String? messageId, String answer) {
    final chatId = _chatId;
    if (chatId == null || answer.isEmpty) return;
    final now = DateTime.now();
    ref.read(chatThreadProvider(chatId).notifier).appendExternal(
          ChatItem(id: 'v-u-${now.microsecondsSinceEpoch}', role: 'user', text: state.transcript, mode: 'voice',
              createdAt: now),
          ChatItem(id: messageId ?? 'v-a-${now.microsecondsSinceEpoch}', role: 'assistant', text: answer, mode: 'voice',
              sources: state.sources, createdAt: now),
        );
  }

  Future<void> _dispose() async {
    await _sub?.cancel();
    await _levelSub?.cancel();
    await _conn?.close();
    await _mic?.dispose();
    await _player?.dispose();
  }
}

final voiceProvider = NotifierProvider<VoiceController, VoiceState>(VoiceController.new);
