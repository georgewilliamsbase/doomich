import 'package:flutter/material.dart';

import '../strings.dart';
import '../theme.dart';
import 'mascot.dart';

class EmptyState extends StatelessWidget {
  const EmptyState({super.key, required this.text, this.action, this.mood = MascotMood.calm});

  final String text;
  final Widget? action;
  final MascotMood mood;

  @override
  Widget build(BuildContext context) => Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(Gaps.l),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Mascot(size: 96, mood: mood),
              const SizedBox(height: Gaps.m),
              Text(text, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodyLarge),
              if (action != null) ...[const SizedBox(height: Gaps.m), action!],
            ]),
          ),
        ),
      );
}

class ErrorView extends StatelessWidget {
  const ErrorView({super.key, required this.error, this.onRetry});

  final Object error;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) => EmptyState(
        text: errorText(context.s, error),
        mood: MascotMood.thinking,
        action: onRetry == null ? null : FilledButton.tonal(onPressed: onRetry, child: Text(context.s.retry)),
      );
}

class LoadingView extends StatelessWidget {
  const LoadingView({super.key});

  @override
  Widget build(BuildContext context) => const Center(child: CircularProgressIndicator());
}

/// Плашка "без сети, обновлено ...".
class OfflineBanner extends StatelessWidget {
  const OfflineBanner({super.key, this.updated});

  final DateTime? updated;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final time = updated == null ? '' : '${updated!.day.toString().padLeft(2, '0')}.${updated!.month.toString().padLeft(2, '0')} ${hhmm(updated!)}';
    return Material(
      color: scheme.tertiaryContainer,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: Gaps.m, vertical: Gaps.s),
        child: Row(children: [
          Icon(Icons.cloud_off, size: 18, color: scheme.onTertiaryContainer),
          const SizedBox(width: Gaps.s),
          Expanded(child: Text(context.s.offlineUpdated(time), style: TextStyle(color: scheme.onTertiaryContainer))),
        ]),
      ),
    );
  }
}

/// Ограничение ширины контента на больших экранах.
class Readable extends StatelessWidget {
  const Readable({super.key, required this.child, this.maxWidth = Gaps.readable});

  final Widget child;
  final double maxWidth;

  @override
  Widget build(BuildContext context) =>
      Center(child: ConstrainedBox(constraints: BoxConstraints(maxWidth: maxWidth), child: child));
}

void showError(BuildContext context, Object error) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(errorText(context.s, error))));
}

void showInfo(BuildContext context, String text) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(text)));
}

Future<bool> confirm(BuildContext context, {required String title, String? body, String? action}) async {
  final res = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: Text(title),
      content: body == null ? null : Text(body),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(context.s.cancel)),
        FilledButton(onPressed: () => Navigator.pop(ctx, true), child: Text(action ?? context.s.ok)),
      ],
    ),
  );
  return res ?? false;
}
