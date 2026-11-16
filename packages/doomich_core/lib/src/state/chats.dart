import 'dart:async';
import 'dart:convert';

import 'package:doomich_api/doomich_api.dart';
import 'package:drift/drift.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/app_db.dart';
import 'app.dart';
import 'schedule.dart';

/// Список чатов с кэшем на устройстве.
class ChatList extends AsyncNotifier<List<ChatOut>> {
  @override
  Future<List<ChatOut>> build() async {
    final api = ref.read(apiClientProvider);
    final db = ref.read(dbProvider);
    try {
      final chats = await api.chats(limit: 200);
      try {
        // Кэш списка чатов для чтения без сети
        await db.transaction(() async {
          await db.delete(db.cachedChats).go();
          for (final c in chats) {
            await db.into(db.cachedChats).insert(CachedChatsCompanion.insert(
                id: c.id, title: Value(c.title), updatedAt: c.updatedAt, documentIds: Value(c.documentIds.join(','))));
          }
        });
      } catch (_) {}
      return chats;
    } on ApiException catch (e) {
      if (!e.isNetwork) rethrow;
      final rows = await (db.select(db.cachedChats)..orderBy([(t) => OrderingTerm.desc(t.updatedAt)])).get();
      return rows
          .map((r) => ChatOut(
              id: r.id, title: r.title, documentIds: r.documentIds.isEmpty ? [] : r.documentIds.split(','),
              createdAt: r.updatedAt, updatedAt: r.updatedAt))
          .toList();
    }
  }

  Future<ChatOut> create({String? title, List<String> documentIds = const [], String? lectureId}) async {
    final chat = await ref.read(apiClientProvider).createChat(title: title, documentIds: documentIds, lectureId: lectureId);
    state = AsyncData([chat, ...?state.value]);
    return chat;
  }

  Future<void> rename(String id, String title) async {
    final chat = await ref.read(apiClientProvider).renameChat(id, title);
    state = AsyncData([for (final c in state.value ?? <ChatOut>[]) c.id == id ? chat : c]);
  }

  Future<void> remove(String id) async {
    await ref.read(apiClientProvider).deleteChat(id);
    final db = ref.read(dbProvider);
    await (db.delete(db.cachedMessages)..where((t) => t.chatId.equals(id))).go();
    await (db.delete(db.cachedChats)..where((t) => t.id.equals(id))).go();
    state = AsyncData([for (final c in state.value ?? <ChatOut>[]) if (c.id != id) c]);
  }

  void touch(String id, {String? title}) {
    final list = [...?state.value];
    final i = list.indexWhere((c) => c.id == id);
    if (i < 0) {
      ref.invalidateSelf();
      return;
    }
    final c = list.removeAt(i);
    list.insert(0, ChatOut(id: c.id, title: c.title ?? title, documentIds: c.documentIds, lectureId: c.lectureId,
        courseId: c.courseId, createdAt: c.createdAt, updatedAt: DateTime.now(), expiresAt: c.expiresAt));
    state = AsyncData(list);
  }
}

final chatListProvider = AsyncNotifierProvider<ChatList, List<ChatOut>>(ChatList.new);

/// Сообщение в ленте: с сервера или ещё генерируемое.
class ChatItem {
  const ChatItem({
    required this.id,
    required this.role,
    required this.text,
    this.sources = const [],
    this.mode = 'text',
    this.pending = false,
    this.modelVersion,
    this.createdAt,
    this.error,
  });

  final String id;
  final String role;
  final String text;
  final List<Source> sources;
  final String mode;
  final bool pending;
  final String? modelVersion;
  final DateTime? createdAt;
  final String? error;

  bool get isUser => role == 'user';

  ChatItem copyWith({String? text, List<Source>? sources, bool? pending, String? id, String? error,
      String? modelVersion}) =>
      ChatItem(id: id ?? this.id, role: role, text: text ?? this.text, sources: sources ?? this.sources, mode: mode,
          pending: pending ?? this.pending, modelVersion: modelVersion ?? this.modelVersion, createdAt: createdAt,
          error: error ?? this.error);

  static ChatItem fromMessage(MessageOut m) => ChatItem(id: m.id, role: m.role, text: m.content, sources: m.sources,
      mode: m.mode, modelVersion: m.modelVersion, createdAt: m.createdAt);
}

class ChatThreadState {
  const ChatThreadState({this.items = const [], this.loading = false, this.sending = false, this.tool, this.error,
      this.offline = false});

  final List<ChatItem> items;
  final bool loading;
  final bool sending;

  /// Чем сейчас занят ассистент: "get_schedule", "search_documents"...
  final String? tool;
  final String? error;
  final bool offline;

  ChatThreadState copyWith({List<ChatItem>? items, bool? loading, bool? sending, Object? tool = _keep,
      Object? error = _keep, bool? offline}) =>
      ChatThreadState(
        items: items ?? this.items,
        loading: loading ?? this.loading,
        sending: sending ?? this.sending,
        tool: identical(tool, _keep) ? this.tool : tool as String?,
        error: identical(error, _keep) ? this.error : error as String?,
        offline: offline ?? this.offline,
      );
}

const _keep = Object();

/// Ключ ленты: id чата или "incognito".
const incognitoChat = 'incognito';

class ChatThread extends Notifier<ChatThreadState> {
  ChatThread(this.chatId);

  final String chatId;
  CancelToken? _cancel;

  bool get isIncognito => chatId == incognitoChat;

  @override
  ChatThreadState build() {
    ref.onDispose(() => _cancel?.cancel());
    if (!isIncognito) Future.microtask(load);
    return ChatThreadState(loading: !isIncognito);
  }

  Future<void> load() async {
    final api = ref.read(apiClientProvider);
    final db = ref.read(dbProvider);
    try {
      final msgs = await api.messages(chatId, limit: 100);
      state = state.copyWith(items: msgs.map(ChatItem.fromMessage).toList(), loading: false, offline: false);
      try {
        await _cache(msgs);
      } catch (_) {}
    } on ApiException catch (e) {
      if (e.isNetwork) {
        final rows = await (db.select(db.cachedMessages)
              ..where((t) => t.chatId.equals(chatId))
              ..orderBy([(t) => OrderingTerm.asc(t.createdAt)]))
            .get();
        state = state.copyWith(loading: false, offline: true, items: rows
            .map((r) => ChatItem(id: r.id, role: r.role, text: r.content, mode: r.mode, createdAt: r.createdAt,
                sources: (jsonDecode(r.sourcesJson) as List<dynamic>)
                    .map((x) => Source.fromJson(x as Map<String, dynamic>))
                    .toList()))
            .toList());
      } else {
        state = state.copyWith(loading: false, error: e.code);
      }
    }
  }

  Future<void> _cache(List<MessageOut> msgs) async {
    final db = ref.read(dbProvider);
    await db.batch((b) {
      for (final m in msgs) {
        b.insert(
          db.cachedMessages,
          CachedMessagesCompanion.insert(id: m.id, chatId: chatId, role: m.role, content: m.content, mode: m.mode,
              createdAt: m.createdAt, sourcesJson: Value(jsonEncode(m.sources.map((s) => s.toJson()).toList()))),
          mode: InsertMode.insertOrReplace,
        );
      }
    });
  }

  ClientContextIn _context() {
    final s = ref.read(settingsProvider);
    return ClientContextIn(groupId: s.deviceGroupId, subgroup: s.deviceSubgroup, teacherKey: s.teacherKey);
  }

  /// Отправить вопрос. [documentIds] сужает поиск до выбранных документов.
  Future<void> send(String text, {String mode = 'text', List<String>? documentIds}) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty || state.sending) return;
    final now = DateTime.now();
    final userItem = ChatItem(id: 'local-${now.microsecondsSinceEpoch}', role: 'user', text: trimmed, mode: mode,
        createdAt: now);
    final draft = ChatItem(id: 'draft', role: 'assistant', text: '', pending: true, mode: mode, createdAt: now);
    final history = [
      for (final i in state.items)
        if (!i.pending && i.error == null) HistoryMessage(role: i.role, content: i.text),
    ];
    state = state.copyWith(items: [...state.items, userItem, draft], sending: true, error: null, tool: null);
    final api = ref.read(apiClientProvider);
    _cancel = CancelToken();
    final Stream<ChatEvent> events = isIncognito
        ? api.sendIncognito(
            IncognitoIn(text: trimmed, mode: mode, documentIds: documentIds, context: _context(),
                history: history.length > 20 ? history.sublist(history.length - 20) : history),
            cancel: _cancel)
        : api.sendMessage(chatId, MessageIn(text: trimmed, mode: mode, documentIds: documentIds, context: _context()),
            cancel: _cancel);
    await _consume(events, userItem.id);
    if (!isIncognito) ref.read(chatListProvider.notifier).touch(chatId, title: trimmed);
  }

  Future<void> retry() async {
    if (state.sending || isIncognito) return;
    final items = [...state.items];
    if (items.isNotEmpty && !items.last.isUser) items.removeLast();
    final draft = ChatItem(id: 'draft', role: 'assistant', text: '', pending: true, createdAt: DateTime.now());
    state = state.copyWith(items: [...items, draft], sending: true, error: null);
    _cancel = CancelToken();
    await _consume(ref.read(apiClientProvider).retry(chatId, cancel: _cancel), null);
  }

  Future<void> _consume(Stream<ChatEvent> events, String? localUserId) async {
    final buf = StringBuffer();
    var sources = <Source>[];
    String? assistantId;
    String? model;
    try {
      await for (final ev in events) {
        switch (ev) {
          case ChatMeta(:final assistantMessageId, :final userMessageId):
            assistantId = assistantMessageId;
            if (localUserId != null && userMessageId != null) _replaceId(localUserId, userMessageId);
          case ChatTool(:final name, :final status):
            state = state.copyWith(tool: status == 'start' ? name : null);
          case ChatDelta(:final text):
            buf.write(text);
            _updateDraft(buf.toString(), sources);
          case ChatSources(:final items):
            sources = items;
            _updateDraft(buf.toString(), sources);
          case ChatDone(:final messageId, :final modelVersion):
            assistantId = messageId ?? assistantId;
            model = modelVersion;
          case ChatError(:final code):
            state = state.copyWith(error: code);
          case ChatUnknown():
            break;
        }
      }
    } on ApiException catch (e) {
      state = state.copyWith(error: e.code);
    }
    final items = [...state.items];
    final i = items.indexWhere((x) => x.id == 'draft');
    if (i >= 0) {
      if (buf.isEmpty) {
        items.removeAt(i);
      } else {
        items[i] = items[i].copyWith(id: assistantId ?? 'local-a-${DateTime.now().microsecondsSinceEpoch}',
            text: buf.toString(), sources: sources, pending: false, modelVersion: model);
      }
    }
    state = state.copyWith(items: items, sending: false, tool: null);
  }

  void _updateDraft(String text, List<Source> sources) {
    state = state.copyWith(items: [
      for (final x in state.items) x.id == 'draft' ? x.copyWith(text: text, sources: sources) : x,
    ]);
  }

  void _replaceId(String from, String to) {
    state = state.copyWith(items: [for (final x in state.items) x.id == from ? x.copyWith(id: to) : x]);
  }

  /// Остановить генерацию. Сервер сохранит уже сгенерированную часть.
  void stop() {
    _cancel?.cancel('stopped');
  }

  /// Для голосового режима: ответ уже пришёл через голосовой канал, добавляем его в ленту.
  void appendExternal(ChatItem user, ChatItem assistant) {
    state = state.copyWith(items: [...state.items, user, assistant]);
  }

  Future<void> feedback(ChatItem item, int rating, {String? comment, String? category, bool share = false}) async {
    final question = () {
      final idx = state.items.indexOf(item);
      for (var i = idx - 1; i >= 0; i--) {
        if (state.items[i].isUser) return state.items[i].text;
      }
      return null;
    }();
    await ref.read(apiClientProvider).feedback(FeedbackIn(
          rating: rating,
          messageId: item.id.startsWith('local') || isIncognito ? null : item.id,
          comment: comment,
          category: category,
          shareContent: share,
          question: share ? question : null,
          answer: share ? item.text : null,
          modelVersion: item.modelVersion,
          mode: item.mode,
        ));
  }
}

final chatThreadProvider =
    NotifierProvider.autoDispose.family<ChatThread, ChatThreadState, String>(ChatThread.new);

/// Ключ расписания для инструментов ассистента берётся из настроек устройства (см. schedule.dart).
final assistantContextProvider = Provider<ClientContextIn>((ref) {
  final s = ref.watch(settingsProvider);
  final scope = ref.watch(scheduleScopeProvider);
  return ClientContextIn(groupId: s.deviceGroupId, subgroup: s.deviceSubgroup, teacherKey: scope?.teacherKey);
});
