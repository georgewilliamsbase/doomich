import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import 'models.g.dart';

/// Параметры начала реплики (сообщение start, см. docs/api/voice-protocol.md).
class VoiceStart {
  const VoiceStart({
    this.lang = 'auto',
    this.chatId,
    this.mode = 'ptt',
    this.codec = 'pcm16',
    this.sampleRate = 16000,
    this.tts = true,
    this.voice,
    this.speed = 1.0,
    this.context,
    this.text,
    this.formats = const ['wav'],
  });

  final String lang;
  final String? chatId;
  final String mode;
  final String codec;
  final int sampleRate;
  final bool tts;
  final String? voice;
  final double speed;
  final ClientContextIn? context;
  final String? text;

  /// Форматы аудио, которые умеет играть клиент, в порядке предпочтения.
  final List<String> formats;

  Map<String, dynamic> toJson() => {
        'type': 'start',
        'lang': lang,
        'chat_id': ?chatId,
        'mode': mode,
        'codec': codec,
        'sample_rate': sampleRate,
        'tts': tts,
        'voice': ?voice,
        'speed': speed,
        'context': ?context?.toJson(),
        'text': ?text,
        'formats': formats,
      };
}

sealed class VoiceEvent {
  const VoiceEvent();
}

class VoiceReady extends VoiceEvent {
  const VoiceReady();
}

class VoiceTranscript extends VoiceEvent {
  const VoiceTranscript(this.text, {this.isFinal = true});
  final String text;
  final bool isFinal;
}

class VoiceAnswerDelta extends VoiceEvent {
  const VoiceAnswerDelta(this.text);
  final String text;
}

class VoiceTool extends VoiceEvent {
  const VoiceTool(this.name, this.status);
  final String name;
  final String status;
}

/// Озвученное предложение: порядковый номер, формат, текст и сами байты файла.
class VoiceAudio extends VoiceEvent {
  const VoiceAudio({required this.seq, required this.format, required this.bytes, this.text, this.duration});
  final int seq;
  final String format;
  final Uint8List bytes;
  final String? text;
  final double? duration;
}

class VoiceSources extends VoiceEvent {
  const VoiceSources(this.items);
  final List<Source> items;
}

class VoiceDone extends VoiceEvent {
  const VoiceDone({this.messageId, this.chatId, this.text = '', this.timings = const {}});
  final String? messageId;
  final String? chatId;
  final String text;
  final Map<String, double> timings;
}

class VoiceError extends VoiceEvent {
  const VoiceError(this.code, this.message);
  final String code;
  final String message;
}

class VoiceCancelled extends VoiceEvent {
  const VoiceCancelled();
}

const _audioFrame = 0x41;
const _formats = {1: 'wav', 2: 'ogg_opus'};

/// Разбор бинарного кадра сервера: 0x41, seq (uint32 BE), формат, данные.
VoiceAudio? parseAudioFrame(Uint8List data, Map<int, Map<String, dynamic>> meta) {
  if (data.length < 6 || data[0] != _audioFrame) return null;
  final seq = ByteData.sublistView(data, 1, 5).getUint32(0, Endian.big);
  final format = _formats[data[5]] ?? 'wav';
  final m = meta.remove(seq) ?? const {};
  return VoiceAudio(
    seq: seq,
    format: format,
    bytes: Uint8List.sublistView(data, 6),
    text: m['text'] as String?,
    duration: (m['duration'] as num?)?.toDouble(),
  );
}

VoiceEvent? parseVoiceMessage(Map<String, dynamic> j, Map<int, Map<String, dynamic>> meta) {
  switch (j['type']) {
    case 'ready':
      return const VoiceReady();
    case 'transcript':
      return VoiceTranscript(j['text'] as String? ?? '', isFinal: j['final'] as bool? ?? true);
    case 'answer_delta':
      return VoiceAnswerDelta(j['text'] as String? ?? '');
    case 'tool':
      return VoiceTool(j['name'] as String? ?? '', j['status'] as String? ?? '');
    case 'audio_meta':
      meta[(j['seq'] as num).toInt()] = j;
      return null;
    case 'sources':
      return VoiceSources((j['items'] as List<dynamic>? ?? const [])
          .map((e) => Source.fromJson(e as Map<String, dynamic>))
          .toList());
    case 'done':
      return VoiceDone(
        messageId: j['message_id'] as String?,
        chatId: j['chat_id'] as String?,
        text: j['text'] as String? ?? '',
        timings: (j['timings'] as Map? ?? const {}).map((k, v) => MapEntry(k as String, (v as num).toDouble())),
      );
    case 'error':
      return VoiceError(j['code'] as String? ?? 'internal', j['message'] as String? ?? '');
    case 'cancelled':
      return const VoiceCancelled();
    default:
      return null;
  }
}

/// Соединение с голосовым шлюзом. Одно соединение живёт, пока открыт голосовой режим.
class VoiceConnection {
  VoiceConnection._(this._channel) {
    _sub = _channel.stream.listen(_onData, onError: _events.addError, onDone: _events.close);
  }

  final WebSocketChannel _channel;
  final _events = StreamController<VoiceEvent>.broadcast();
  final _meta = <int, Map<String, dynamic>>{};
  late final StreamSubscription<dynamic> _sub;

  Stream<VoiceEvent> get events => _events.stream;

  static Future<VoiceConnection> connect(Uri uri, String accessToken) async {
    final channel = IOWebSocketChannel.connect(uri, headers: {'Authorization': 'Bearer $accessToken'},
        pingInterval: const Duration(seconds: 20));
    await channel.ready;
    return VoiceConnection._(channel);
  }

  /// Для тестов и нестандартных транспортов.
  static VoiceConnection fromChannel(WebSocketChannel channel) => VoiceConnection._(channel);

  void _onData(dynamic data) {
    if (data is List<int>) {
      final audio = parseAudioFrame(data is Uint8List ? data : Uint8List.fromList(data), _meta);
      if (audio != null) _events.add(audio);
      return;
    }
    final j = jsonDecode(data as String) as Map<String, dynamic>;
    final ev = parseVoiceMessage(j, _meta);
    if (ev != null) _events.add(ev);
  }

  void start(VoiceStart s) => _channel.sink.add(jsonEncode(s.toJson()));

  void audio(Uint8List pcm) => _channel.sink.add(pcm);

  void end() => _channel.sink.add(jsonEncode({'type': 'end'}));

  void cancel() => _channel.sink.add(jsonEncode({'type': 'cancel'}));

  Future<void> close() async {
    await _sub.cancel();
    await _channel.sink.close();
    await _events.close();
  }
}
