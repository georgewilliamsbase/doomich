import 'package:doomich_api/doomich_api.dart';
import 'package:doomich_core/doomich_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:gpt_markdown/gpt_markdown.dart';

import '../strings.dart';
import '../theme.dart';

/// Сообщение в ленте. Ответ ассистента рендерится как Markdown с формулами LaTeX и кодом.
class MessageBubble extends StatelessWidget {
  const MessageBubble({
    super.key,
    required this.item,
    this.tool,
    this.onSource,
    this.onFeedback,
    this.onSpeak,
    this.onRetry,
  });

  final ChatItem item;
  final String? tool;
  final void Function(Source s)? onSource;
  final void Function(int rating)? onFeedback;
  final VoidCallback? onSpeak;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final isUser = item.isUser;
    final s = context.s;
    final bubble = Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: isUser ? scheme.primaryContainer : scheme.surfaceContainerHigh,
        borderRadius: BorderRadius.only(
          topLeft: const Radius.circular(18),
          topRight: const Radius.circular(18),
          bottomLeft: Radius.circular(isUser ? 18 : 4),
          bottomRight: Radius.circular(isUser ? 4 : 18),
        ),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        if (item.mode == 'voice')
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Icon(Icons.mic, size: 14, color: scheme.onSurfaceVariant),
          ),
        if (isUser)
          SelectableText(item.text, style: TextStyle(color: scheme.onPrimaryContainer))
        else if (item.pending && item.text.isEmpty)
          _Thinking(text: tool == null ? s.thinking : toolText(s, tool!))
        else
          SelectionArea(child: GptMarkdown(item.text, style: Theme.of(context).textTheme.bodyMedium)),
        if (item.pending && item.text.isNotEmpty && tool != null)
          Padding(padding: const EdgeInsets.only(top: 6), child: _Thinking(text: toolText(s, tool!))),
      ]),
    );
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: MediaQuery.sizeOf(context).width * (isUser ? 0.8 : 0.92)),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: Gaps.xs),
          child: Column(
            crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
            children: [
              Semantics(label: isUser ? null : s.appName, child: bubble),
              if (!isUser && item.sources.isNotEmpty) _Sources(sources: item.sources, onTap: onSource),
              if (!isUser && !item.pending && item.text.isNotEmpty)
                _Actions(item: item, onFeedback: onFeedback, onSpeak: onSpeak, onRetry: onRetry),
            ],
          ),
        ),
      ),
    );
  }
}

class _Thinking extends StatelessWidget {
  const _Thinking({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
        const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2)),
        const SizedBox(width: 8),
        Text(text, style: Theme.of(context).textTheme.bodySmall),
      ]);
}

class _Sources extends StatelessWidget {
  const _Sources({required this.sources, this.onTap});

  final List<Source> sources;
  final void Function(Source s)? onTap;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return Padding(
      padding: const EdgeInsets.only(top: Gaps.xs),
      child: Wrap(spacing: 6, runSpacing: 6, children: [
        for (final src in sources)
          ActionChip(
            avatar: CircleAvatar(child: Text('${src.n}', style: const TextStyle(fontSize: 11))),
            label: Text([
              src.title,
              if (src.page != null) s.page('${src.page}'),
              if (src.sheet != null) s.sheet(src.sheet!),
            ].join(', '), overflow: TextOverflow.ellipsis),
            onPressed: onTap == null ? null : () => onTap!(src),
            tooltip: src.snippet,
          ),
      ]),
    );
  }
}

class _Actions extends StatelessWidget {
  const _Actions({required this.item, this.onFeedback, this.onSpeak, this.onRetry});

  final ChatItem item;
  final void Function(int rating)? onFeedback;
  final VoidCallback? onSpeak;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return Row(mainAxisSize: MainAxisSize.min, children: [
      IconButton(
        visualDensity: VisualDensity.compact,
        tooltip: s.copy,
        icon: const Icon(Icons.copy, size: 18),
        onPressed: () async {
          await Clipboard.setData(ClipboardData(text: item.text));
          if (context.mounted) showSnack(context, s.copied);
        },
      ),
      if (onSpeak != null)
        IconButton(visualDensity: VisualDensity.compact, tooltip: s.speak, icon: const Icon(Icons.volume_up, size: 18),
            onPressed: onSpeak),
      if (onFeedback != null) ...[
        IconButton(visualDensity: VisualDensity.compact, tooltip: s.feedbackGood,
            icon: const Icon(Icons.thumb_up_outlined, size: 18), onPressed: () => onFeedback!(1)),
        IconButton(visualDensity: VisualDensity.compact, tooltip: s.feedbackBad,
            icon: const Icon(Icons.thumb_down_outlined, size: 18), onPressed: () => onFeedback!(-1)),
      ],
      if (onRetry != null)
        IconButton(visualDensity: VisualDensity.compact, tooltip: s.retry, icon: const Icon(Icons.refresh, size: 18),
            onPressed: onRetry),
    ]);
  }
}

void showSnack(BuildContext context, String text) =>
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text), duration: const Duration(seconds: 2)));
