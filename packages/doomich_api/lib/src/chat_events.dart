import 'models.g.dart';

/// События потока ответа ассистента.
sealed class ChatEvent {
  const ChatEvent();

  static ChatEvent fromSse(String event, Map<String, dynamic> j) {
    switch (event) {
      case 'meta':
        return ChatMeta(
          chatId: j['chat_id'] as String?,
          userMessageId: j['user_message_id'] as String?,
          assistantMessageId: j['assistant_message_id'] as String?,
        );
      case 'tool':
        return ChatTool(j['name'] as String? ?? '', j['status'] as String? ?? '');
      case 'delta':
        return ChatDelta(j['text'] as String? ?? '');
      case 'sources':
        final items = (j['items'] as List<dynamic>? ?? const [])
            .map((e) => Source.fromJson(e as Map<String, dynamic>))
            .toList();
        return ChatSources(items);
      case 'done':
        return ChatDone(
          messageId: j['message_id'] as String?,
          modelVersion: j['model_version'] as String?,
          finishReason: j['finish_reason'] as String? ?? 'stop',
        );
      case 'error':
        return ChatError(j['code'] as String? ?? 'internal', j['message'] as String? ?? '');
      default:
        return ChatUnknown(event);
    }
  }
}

class ChatMeta extends ChatEvent {
  const ChatMeta({this.chatId, this.userMessageId, this.assistantMessageId});
  final String? chatId;
  final String? userMessageId;
  final String? assistantMessageId;
}

class ChatTool extends ChatEvent {
  const ChatTool(this.name, this.status);
  final String name;
  final String status;
}

class ChatDelta extends ChatEvent {
  const ChatDelta(this.text);
  final String text;
}

class ChatSources extends ChatEvent {
  const ChatSources(this.items);
  final List<Source> items;
}

class ChatDone extends ChatEvent {
  const ChatDone({this.messageId, this.modelVersion, this.finishReason = 'stop'});
  final String? messageId;
  final String? modelVersion;
  final String finishReason;
}

class ChatError extends ChatEvent {
  const ChatError(this.code, this.message);
  final String code;
  final String message;
}

class ChatUnknown extends ChatEvent {
  const ChatUnknown(this.event);
  final String event;
}
