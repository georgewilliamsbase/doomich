import 'dart:async';
import 'dart:convert';

/// Одно событие Server-Sent Events.
class SseEvent {
  const SseEvent(this.event, this.data);

  final String event;
  final String data;

  Map<String, dynamic> get json => data.isEmpty ? const {} : jsonDecode(data) as Map<String, dynamic>;
}

/// Разбирает поток байтов text/event-stream в события.
Stream<SseEvent> parseSse(Stream<List<int>> bytes) async* {
  var event = 'message';
  final data = StringBuffer();
  var buffer = '';
  await for (final chunk in utf8.decoder.bind(bytes)) {
    buffer += chunk;
    while (true) {
      final nl = buffer.indexOf('\n');
      if (nl < 0) break;
      var line = buffer.substring(0, nl);
      buffer = buffer.substring(nl + 1);
      if (line.endsWith('\r')) line = line.substring(0, line.length - 1);
      if (line.isEmpty) {
        if (data.isNotEmpty || event != 'message') {
          yield SseEvent(event, data.toString());
        }
        event = 'message';
        data.clear();
      } else if (line.startsWith(':')) {
        continue; // комментарий, например пинг
      } else if (line.startsWith('event:')) {
        event = line.substring(6).trim();
      } else if (line.startsWith('data:')) {
        if (data.isNotEmpty) data.write('\n');
        data.write(line.substring(5).trimLeft());
      }
    }
  }
  if (data.isNotEmpty) yield SseEvent(event, data.toString());
}
