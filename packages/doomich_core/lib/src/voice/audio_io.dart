import 'dart:async';
import 'dart:io';
import 'dart:math' as math;
import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

/// Захват микрофона: PCM16 16 кГц моно потоком, плюс уровень сигнала для индикатора.
class MicRecorder {
  MicRecorder({AudioRecorder? recorder}) : _rec = recorder ?? AudioRecorder();

  final AudioRecorder _rec;
  StreamSubscription<Uint8List>? _sub;
  StreamSubscription<Amplitude>? _ampSub;
  final _level = StreamController<double>.broadcast();

  /// Уровень 0..1 примерно раз в 100 мс.
  Stream<double> get level => _level.stream;

  Future<bool> hasPermission() => _rec.hasPermission();

  Future<List<InputDevice>> devices() => _rec.listInputDevices();

  Future<void> start(void Function(Uint8List chunk) onChunk, {String? deviceId}) async {
    await stop();
    final stream = await _rec.startStream(RecordConfig(
      encoder: AudioEncoder.pcm16bits,
      sampleRate: 16000,
      numChannels: 1,
      echoCancel: true,
      noiseSuppress: true,
      autoGain: true,
      device: deviceId == null ? null : InputDevice(id: deviceId, label: deviceId),
    ));
    _sub = stream.listen(onChunk);
    _ampSub = _rec.onAmplitudeChanged(const Duration(milliseconds: 100)).listen((a) {
      // dBFS -> 0..1, тишина около -60 дБ
      final v = ((a.current + 60) / 60).clamp(0.0, 1.0);
      _level.add(v.isNaN ? 0 : v);
    });
  }

  Future<void> stop() async {
    await _sub?.cancel();
    await _ampSub?.cancel();
    _sub = null;
    _ampSub = null;
    if (await _rec.isRecording()) await _rec.stop();
    _level.add(0);
  }

  Future<void> dispose() async {
    await stop();
    await _level.close();
    await _rec.dispose();
  }
}

/// Очередь воспроизведения озвученных предложений.
/// Каждый кусок пишется во временный файл и удаляется сразу после проигрывания.
class SpeechQueue {
  SpeechQueue({AudioPlayer? player}) : _player = player ?? AudioPlayer() {
    _player.onPlayerComplete.listen((_) => _next());
  }

  final AudioPlayer _player;
  final _queue = <File>[];
  File? _current;
  double _rate = 1.0;
  bool _stopped = false;
  final _idle = StreamController<bool>.broadcast();
  int _counter = 0;

  /// true, когда очередь опустела и звук закончился.
  Stream<bool> get idle => _idle.stream;
  bool get isPlaying => _current != null;

  Future<void> setRate(double rate) async {
    _rate = rate;
    await _player.setPlaybackRate(rate);
  }

  Future<void> enqueue(Uint8List bytes, String format) async {
    _stopped = false;
    final dir = await getTemporaryDirectory();
    final ext = format == 'ogg_opus' ? 'ogg' : 'wav';
    final f = File('${dir.path}/doomich-tts-${DateTime.now().microsecondsSinceEpoch}-${_counter++}.$ext');
    await f.writeAsBytes(bytes, flush: true);
    _queue.add(f);
    if (_current == null) await _next();
  }

  Future<void> _next() async {
    final done = _current;
    _current = null;
    if (done != null) unawaited(done.delete().catchError((_) => done));
    if (_stopped || _queue.isEmpty) {
      _idle.add(true);
      return;
    }
    _current = _queue.removeAt(0);
    try {
      await _player.play(DeviceFileSource(_current!.path));
      if (_rate != 1.0) await _player.setPlaybackRate(_rate);
    } catch (_) {
      await _next();
    }
  }

  /// Прервать озвучку (кнопка "стоп" или перебивание).
  Future<void> stop() async {
    _stopped = true;
    await _player.stop();
    for (final f in _queue) {
      unawaited(f.delete().catchError((_) => f));
    }
    _queue.clear();
    final cur = _current;
    _current = null;
    if (cur != null) unawaited(cur.delete().catchError((_) => cur));
    _idle.add(true);
  }

  Future<void> dispose() async {
    await stop();
    await _idle.close();
    await _player.dispose();
  }
}

/// Простой детектор речи по энергии: останавливает запись после паузы (R1.1).
/// Модель Silero VAD подключается отдельно, если её файл положили в assets.
class EnergyVad {
  EnergyVad({this.silenceMs = 900, this.minSpeechMs = 300, this.threshold = 0.015});

  final int silenceMs;
  final int minSpeechMs;
  final double threshold;
  int _speechMs = 0;
  int _silenceMs = 0;

  void reset() {
    _speechMs = 0;
    _silenceMs = 0;
  }

  /// Возвращает true, когда пора заканчивать запись.
  bool feed(Uint8List pcm16) {
    final samples = pcm16.length ~/ 2;
    if (samples == 0) return false;
    final view = ByteData.sublistView(pcm16);
    var sum = 0.0;
    for (var i = 0; i < samples; i++) {
      final v = view.getInt16(i * 2, Endian.little) / 32768.0;
      sum += v * v;
    }
    final rms = math.sqrt(sum / samples);
    final ms = samples * 1000 ~/ 16000;
    if (rms > threshold) {
      _speechMs += ms;
      _silenceMs = 0;
    } else {
      _silenceMs += ms;
    }
    return _speechMs >= minSpeechMs && _silenceMs >= silenceMs;
  }
}
