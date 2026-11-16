import 'package:doomich_api/doomich_api.dart';
import 'package:doomich_core/doomich_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../routes.dart';
import '../strings.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/mascot.dart';
import '../widgets/message_bubble.dart';
import '../widgets/mic_button.dart';

/// Лента чата с полем ввода. Используется обоими приложениями.
class ChatView extends ConsumerStatefulWidget {
  const ChatView({super.key, required this.chatId, this.documentIds, this.showAppBar = true, this.onOpenSource,
      this.embedded = false});

  final String chatId;
  final List<String>? documentIds;
  final bool showAppBar;
  final void Function(Source s)? onOpenSource;

  /// Чат встроен в правую панель (ПК): без кнопки "назад", курсор сразу в поле ввода
  final bool embedded;

  @override
  ConsumerState<ChatView> createState() => _ChatViewState();
}

class _ChatViewState extends ConsumerState<ChatView> {
  final _input = TextEditingController();
  final _scroll = ScrollController();
  final _focus = FocusNode();

  ChatThread get _thread => ref.read(chatThreadProvider(widget.chatId).notifier);

  bool get _incognito => widget.chatId == incognitoChat;

  void _send([String? preset]) {
    final text = preset ?? _input.text;
    if (text.trim().isEmpty) return;
    final readAloud = ref.read(settingsProvider).readAloud;
    _input.clear();
    if (readAloud && !_incognito) {
      // Озвучка ответа: вопрос уходит через голосовой канал, ответ попадёт в ленту
      ref.read(voiceProvider.notifier).ask(text, chatId: widget.chatId);
    } else {
      _thread.send(text, documentIds: widget.documentIds);
    }
    _focus.requestFocus();
  }

  void _scrollToEnd() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent, duration: const Duration(milliseconds: 200),
            curve: Curves.easeOut);
      }
    });
  }

  Future<void> _feedback(ChatItem item, int rating) async {
    final s = context.s;
    if (rating > 0) {
      await _thread.feedback(item, 1);
      if (mounted) showInfo(context, s.feedbackThanks);
      return;
    }
    final result = await showDialog<(String?, String?, bool)>(context: context, builder: (_) => const _FeedbackDialog());
    if (result == null) return;
    try {
      await _thread.feedback(item, -1, category: result.$1, comment: result.$2, share: result.$3);
      if (mounted) showInfo(context, s.feedbackThanks);
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  void _openSource(Source src) {
    if (widget.onOpenSource != null) {
      widget.onOpenSource!(src);
    } else {
      context.push(Routes.source(src.documentId, src.chunkId));
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final state = ref.watch(chatThreadProvider(widget.chatId));
    final voice = ref.watch(voiceProvider);
    ref.listen(chatThreadProvider(widget.chatId).select((x) => x.items.length), (_, _) => _scrollToEnd());
    ref.listen(chatThreadProvider(widget.chatId).select((x) => x.items.lastOrNull?.text.length), (_, _) => _scrollToEnd());
    ref.listen(chatThreadProvider(widget.chatId).select((x) => x.error), (_, err) {
      if (err != null) showError(context, err);
    });
    ref.listen(voiceProvider.select((v) => v.error), (_, err) {
      if (err != null) showError(context, err);
    });

    final body = Column(children: [
      if (_incognito)
        MaterialBanner(content: Text(s.incognitoHint), leading: const Icon(Icons.visibility_off_outlined),
            actions: const [SizedBox.shrink()]),
      if (state.offline) const OfflineBanner(),
      Expanded(
        child: state.loading
            ? const LoadingView()
            : state.items.isEmpty
                ? _EmptyChat(onPick: _send)
                : ListView.builder(
                    controller: _scroll,
                    padding: const EdgeInsets.symmetric(horizontal: Gaps.m, vertical: Gaps.s),
                    itemCount: state.items.length,
                    itemBuilder: (context, i) {
                      final item = state.items[i];
                      final last = i == state.items.length - 1;
                      return Readable(
                        child: MessageBubble(
                          item: item,
                          tool: item.pending ? state.tool : null,
                          onSource: _openSource,
                          onFeedback: item.isUser ? null : (r) => _feedback(item, r),
                          onSpeak: item.isUser || _incognito ? null : () => ref.read(voiceProvider.notifier)
                              .ask(item.text, chatId: null),
                          onRetry: last && !item.isUser && !_incognito && !state.sending ? _thread.retry : null,
                        ),
                      );
                    },
                  ),
      ),
      if (voice.busy && voice.transcript.isNotEmpty && voice.phase != VoicePhase.speaking)
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: Gaps.m),
          child: Text(voice.transcript, style: Theme.of(context).textTheme.bodySmall),
        ),
      SafeArea(
        top: false,
        child: Readable(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(Gaps.m, Gaps.s, Gaps.m, Gaps.m),
            child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
              Expanded(
                child: CallbackShortcuts(
                  bindings: {
                    const SingleActivator(LogicalKeyboardKey.enter): () => _send(),
                  },
                  child: TextField(
                    controller: _input,
                    focusNode: _focus,
                    autofocus: widget.embedded,
                    minLines: 1,
                    maxLines: 6,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => _send(),
                    decoration: InputDecoration(
                      hintText: s.messageHint,
                      border: const OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(24))),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: Gaps.s),
              if (state.sending)
                IconButton.filledTonal(onPressed: _thread.stop, icon: const Icon(Icons.stop), tooltip: s.stop)
              else
                ValueListenableBuilder(
                  valueListenable: _input,
                  builder: (context, value, _) => value.text.trim().isEmpty
                      ? MicButton(chatId: _incognito ? null : widget.chatId)
                      : IconButton.filled(onPressed: _send, icon: const Icon(Icons.send), tooltip: s.send),
                ),
            ]),
          ),
        ),
      ),
    ]);

    if (!widget.showAppBar) return body;
    return Scaffold(
      appBar: AppBar(
        automaticallyImplyLeading: !widget.embedded,
        title: Text(_incognito ? s.incognito : _title(ref, s)),
        actions: [
          IconButton(
            tooltip: s.readAloud,
            icon: Icon(ref.watch(settingsProvider.select((x) => x.readAloud)) ? Icons.volume_up : Icons.volume_off),
            onPressed: () => ref.read(settingsProvider.notifier).update((x) => x.copyWith(readAloud: !x.readAloud)),
          ),
        ],
      ),
      body: body,
    );
  }

  String _title(WidgetRef ref, S s) {
    final chats = ref.watch(chatListProvider).value ?? const [];
    for (final c in chats) {
      if (c.id == widget.chatId) return c.title ?? s.newChat;
    }
    return s.newChat;
  }
}

class _EmptyChat extends StatelessWidget {
  const _EmptyChat({required this.onPick});

  final void Function(String text) onPick;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return EmptyState(
      text: s.chatEmpty,
      mood: MascotMood.happy,
      action: Wrap(spacing: Gaps.s, runSpacing: Gaps.s, alignment: WrapAlignment.center, children: [
        for (final q in [s.chatSuggest1, s.chatSuggest2, s.chatSuggest3])
          ActionChip(label: Text(q), onPressed: () => onPick(q)),
      ]),
    );
  }
}

class _FeedbackDialog extends StatefulWidget {
  const _FeedbackDialog();

  @override
  State<_FeedbackDialog> createState() => _FeedbackDialogState();
}

class _FeedbackDialogState extends State<_FeedbackDialog> {
  String _category = 'wrong';
  final _comment = TextEditingController();
  bool _share = false;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final options = {
      'wrong': s.feedbackWrong,
      'no_source': s.feedbackNoSource,
      'voice': s.feedbackVoice,
      'other': s.feedbackOther,
    };
    return AlertDialog(
      title: Text(s.feedbackTitle),
      content: SingleChildScrollView(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          RadioGroup<String>(
            groupValue: _category,
            onChanged: (v) => setState(() => _category = v ?? 'other'),
            child: Column(children: [
              for (final e in options.entries) RadioListTile<String>(value: e.key, title: Text(e.value)),
            ]),
          ),
          TextField(controller: _comment, maxLines: 3, decoration: InputDecoration(labelText: s.feedbackComment)),
          CheckboxListTile(value: _share, onChanged: (v) => setState(() => _share = v ?? false),
              title: Text(s.feedbackShare)),
        ]),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: Text(s.cancel)),
        FilledButton(
          onPressed: () => Navigator.pop(context, (_category, _comment.text.trim().isEmpty ? null : _comment.text.trim(), _share)),
          child: Text(s.send),
        ),
      ],
    );
  }
}

/// Список чатов: на телефоне отдельный экран, на ПК левая панель.
class ChatListView extends ConsumerStatefulWidget {
  const ChatListView({super.key, required this.onOpen, this.selectedId, this.dense = false});

  final void Function(String chatId) onOpen;
  final String? selectedId;
  final bool dense;

  @override
  ConsumerState<ChatListView> createState() => _ChatListViewState();
}

class _ChatListViewState extends ConsumerState<ChatListView> {
  String _filter = '';

  Future<void> _newChat() async {
    final s = ref.read(settingsProvider);
    final me = ref.read(meProvider);
    if (s.incognitoByDefault || me?.historyDays == 0) {
      widget.onOpen(incognitoChat);
      return;
    }
    try {
      final chat = await ref.read(chatListProvider.notifier).create();
      widget.onOpen(chat.id);
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  Future<void> _rename(ChatOut chat) async {
    final s = context.s;
    final ctl = TextEditingController(text: chat.title);
    final title = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.rename),
        content: TextField(controller: ctl, autofocus: true),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: Text(s.cancel)),
          FilledButton(onPressed: () => Navigator.pop(ctx, ctl.text.trim()), child: Text(s.save)),
        ],
      ),
    );
    if (title != null && title.isNotEmpty) await ref.read(chatListProvider.notifier).rename(chat.id, title);
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final chats = ref.watch(chatListProvider);
    return Column(children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(Gaps.m, Gaps.s, Gaps.m, Gaps.s),
        child: Row(children: [
          Expanded(
            child: TextField(
              decoration: InputDecoration(hintText: s.search, prefixIcon: const Icon(Icons.search), isDense: true),
              onChanged: (v) => setState(() => _filter = v.toLowerCase()),
            ),
          ),
          const SizedBox(width: Gaps.s),
          IconButton.filledTonal(onPressed: _newChat, icon: const Icon(Icons.add_comment_outlined), tooltip: s.newChat),
          IconButton(onPressed: () => widget.onOpen(incognitoChat), icon: const Icon(Icons.visibility_off_outlined),
              tooltip: s.incognito),
        ]),
      ),
      Expanded(
        child: chats.when(
          loading: () => const LoadingView(),
          error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(chatListProvider)),
          data: (items) {
            final list = items.where((c) => _filter.isEmpty || (c.title ?? '').toLowerCase().contains(_filter)).toList();
            if (list.isEmpty) {
              return EmptyState(text: s.chatEmpty, action: FilledButton(onPressed: _newChat, child: Text(s.newChat)));
            }
            return RefreshIndicator(
              onRefresh: () => ref.refresh(chatListProvider.future),
              child: ListView.builder(
                itemCount: list.length,
                itemBuilder: (context, i) {
                  final c = list[i];
                  return ListTile(
                    dense: widget.dense,
                    selected: c.id == widget.selectedId,
                    leading: Icon(c.documentIds.isNotEmpty ? Icons.description_outlined : Icons.chat_bubble_outline),
                    title: Text(c.title ?? s.newChat, maxLines: 1, overflow: TextOverflow.ellipsis),
                    subtitle: Text(_date(c.updatedAt)),
                    onTap: () => widget.onOpen(c.id),
                    trailing: PopupMenuButton<String>(
                      onSelected: (v) async {
                        if (v == 'rename') await _rename(c);
                        if (v == 'delete' && context.mounted &&
                            await confirm(context, title: s.delete, action: s.delete)) {
                          await ref.read(chatListProvider.notifier).remove(c.id);
                        }
                      },
                      itemBuilder: (_) => [
                        PopupMenuItem(value: 'rename', child: Text(s.rename)),
                        PopupMenuItem(value: 'delete', child: Text(s.delete)),
                      ],
                    ),
                  );
                },
              ),
            );
          },
        ),
      ),
    ]);
  }

  String _date(DateTime d) {
    final l = d.toLocal();
    final now = DateTime.now();
    if (l.year == now.year && l.month == now.month && l.day == now.day) return hhmm(l);
    return '${l.day.toString().padLeft(2, '0')}.${l.month.toString().padLeft(2, '0')}';
  }
}

/// Полноэкранный голосовой режим (телефон).
class VoiceScreen extends ConsumerStatefulWidget {
  const VoiceScreen({super.key, this.chatId});

  final String? chatId;

  @override
  ConsumerState<VoiceScreen> createState() => _VoiceScreenState();
}

class _VoiceScreenState extends ConsumerState<VoiceScreen> {
  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final v = ref.watch(voiceProvider);
    final status = switch (v.phase) {
      VoicePhase.listening => s.listening,
      VoicePhase.thinking || VoicePhase.connecting => v.tool == null ? s.thinking : toolText(s, v.tool!),
      VoicePhase.speaking => s.speaking,
      VoicePhase.idle => ref.watch(settingsProvider).holdToTalk ? s.holdToTalk : s.tapToTalk,
    };
    final mood = switch (v.phase) {
      VoicePhase.listening => MascotMood.listening,
      VoicePhase.thinking || VoicePhase.connecting => MascotMood.thinking,
      _ => MascotMood.happy,
    };
    return Scaffold(
      appBar: AppBar(leading: IconButton(icon: const Icon(Icons.close), onPressed: () {
        ref.read(voiceProvider.notifier).cancel();
        context.pop();
      })),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(Gaps.l),
          child: Column(children: [
            const Spacer(),
            Mascot(size: 140, mood: mood),
            const SizedBox(height: Gaps.l),
            Text(status, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: Gaps.m),
            if (v.transcript.isNotEmpty)
              Text('"${v.transcript}"', textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodyLarge),
            const SizedBox(height: Gaps.m),
            if (v.answer.isNotEmpty)
              Flexible(child: SingleChildScrollView(child: Text(v.answer, textAlign: TextAlign.center))),
            const Spacer(),
            MicButton(chatId: widget.chatId, size: 88),
            const SizedBox(height: Gaps.l),
          ]),
        ),
      ),
    );
  }
}
