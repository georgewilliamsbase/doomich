import 'dart:io';
import 'dart:typed_data';

import 'package:doomich_api/doomich_api.dart';
import 'package:doomich_core/doomich_core.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../routes.dart';
import '../strings.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/lesson_tile.dart';

/// Расписание: сегодня, неделя, "сейчас и далее", работа без сети.
class ScheduleView extends ConsumerStatefulWidget {
  const ScheduleView({super.key, this.showAppBar = true});

  final bool showAppBar;

  @override
  ConsumerState<ScheduleView> createState() => _ScheduleViewState();
}

class _ScheduleViewState extends ConsumerState<ScheduleView> {
  DateTime _day = DateTime.now();
  bool _week = false;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final scope = ref.watch(scheduleScopeProvider);
    final locale = Localizations.localeOf(context).languageCode;
    final weekStart = mondayOf(_day);
    final schedule = ref.watch(scheduleProvider(weekStart));
    final body = scope == null
        ? EmptyState(text: s.noGroup,
            action: FilledButton(onPressed: () => context.push('${Routes.group}?from=settings'), child: Text(s.chooseGroup)))
        : schedule.when(
            loading: () => const LoadingView(),
            error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(scheduleProvider(weekStart))),
            data: (week) => RefreshIndicator(
              onRefresh: () => ref.refresh(scheduleProvider(weekStart).future),
              child: ListView(padding: const EdgeInsets.all(Gaps.m), children: [
                if (week.offline) ...[OfflineBanner(updated: week.fetchedAt), const SizedBox(height: Gaps.s)],
                _NowNext(week: week),
                const SizedBox(height: Gaps.m),
                if (_week)
                  for (var i = 0; i < 7; i++) ..._dayBlock(context, week, weekStart.add(Duration(days: i)), locale)
                else
                  ..._dayBlock(context, week, _day, locale, header: false),
              ]),
            ),
          );

    final controls = Padding(
      padding: const EdgeInsets.symmetric(horizontal: Gaps.m, vertical: Gaps.s),
      child: Row(children: [
        IconButton(icon: const Icon(Icons.chevron_left), tooltip: s.back,
            onPressed: () => setState(() => _day = _day.subtract(Duration(days: _week ? 7 : 1)))),
        Expanded(
          child: TextButton(
            onPressed: () => setState(() => _day = DateTime.now()),
            child: Text(_week
                ? '${DateFormat.MMMd(locale).format(weekStart)} - ${DateFormat.MMMd(locale).format(weekStart.add(const Duration(days: 6)))}'
                : _dayTitle(s, _day, locale)),
          ),
        ),
        IconButton(icon: const Icon(Icons.chevron_right), tooltip: s.next,
            onPressed: () => setState(() => _day = _day.add(Duration(days: _week ? 7 : 1)))),
        SegmentedButton<bool>(
          showSelectedIcon: false,
          segments: [ButtonSegment(value: false, label: Text(s.day)), ButtonSegment(value: true, label: Text(s.week))],
          selected: {_week},
          onSelectionChanged: (v) => setState(() => _week = v.first),
        ),
      ]),
    );
    final content = Column(children: [controls, Expanded(child: body)]);
    if (!widget.showAppBar) return content;
    return Scaffold(
      appBar: AppBar(
        title: Text(scope == null ? s.tabSchedule : '${s.tabSchedule}: ${scope.title}'),
        actions: [
          IconButton(icon: const Icon(Icons.groups_outlined), tooltip: s.chooseGroup,
              onPressed: () => context.push('${Routes.group}?from=settings')),
        ],
      ),
      body: content,
    );
  }

  String _dayTitle(S s, DateTime d, String locale) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final day = DateTime(d.year, d.month, d.day);
    final diff = day.difference(today).inDays;
    final label = diff == 0 ? s.today : (diff == 1 ? s.tomorrow : DateFormat.EEEE(locale).format(d));
    return '$label, ${DateFormat.MMMd(locale).format(d)}';
  }

  List<Widget> _dayBlock(BuildContext context, WeekSchedule week, DateTime day, String locale, {bool header = true}) {
    final s = context.s;
    final lessons = week.forDay(day);
    final now = DateTime.now();
    return [
      if (header)
        Padding(
          padding: const EdgeInsets.only(top: Gaps.m, bottom: Gaps.s),
          child: Text(_dayTitle(s, day, locale), style: Theme.of(context).textTheme.titleSmall),
        ),
      if (lessons.isEmpty)
        Padding(padding: const EdgeInsets.symmetric(vertical: Gaps.s), child: Text(s.noLessons))
      else
        for (final l in lessons)
          Padding(
            padding: const EdgeInsets.only(bottom: Gaps.s),
            child: LessonTile(lesson: l, offsetMinutes: week.offsetMinutes,
                highlight: !l.startsAt.toLocal().isAfter(now) && l.endsAt.toLocal().isAfter(now)),
          ),
    ];
  }
}

class _NowNext extends StatelessWidget {
  const _NowNext({required this.week});

  final WeekSchedule week;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final (cur, next) = week.nowNext(DateTime.now());
    if (cur == null && next == null) return const SizedBox.shrink();
    final off = week.offsetMinutes;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Gaps.m),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          if (cur != null) ...[
            Text(s.nowLesson, style: Theme.of(context).textTheme.labelLarge),
            Text('${cur.subject} · ${hhmm(cur.startsAt, off)}-${hhmm(cur.endsAt, off)}'
                '${cur.room == null ? '' : ' · ${s.room(cur.room!)}'}'),
            const SizedBox(height: Gaps.s),
          ],
          if (next != null) ...[
            Text(s.nextLesson, style: Theme.of(context).textTheme.labelLarge),
            Text('${next.subject} · ${DateFormat.E(Localizations.localeOf(context).languageCode).format(week.campus(next.startsAt))} '
                '${hhmm(next.startsAt, off)}${next.room == null ? '' : ' · ${s.room(next.room!)}'}'),
          ],
        ]),
      ),
    );
  }
}

/// Документы пользователя: загрузка, статусы обработки, "спросить по документу", удаление.
class DocumentsView extends ConsumerStatefulWidget {
  const DocumentsView({super.key, required this.onAsk, this.showAppBar = true, this.initialFiles = const []});

  /// Открыть чат по документу
  final void Function(String chatId) onAsk;
  final bool showAppBar;

  /// Файлы, пришедшие через "Поделиться" на Android
  final List<String> initialFiles;

  @override
  ConsumerState<DocumentsView> createState() => _DocumentsViewState();
}

class _DocumentsViewState extends ConsumerState<DocumentsView> {
  UploadProgress? _progress;

  @override
  void initState() {
    super.initState();
    if (widget.initialFiles.isNotEmpty) {
      Future.microtask(() async {
        for (final p in widget.initialFiles) {
          await _upload(p.split(Platform.pathSeparator).last, path: p);
        }
      });
    }
  }

  Future<void> _pick() async {
    final res = await FilePicker.pickFiles(type: FileType.custom, allowedExtensions: ['pdf', 'docx', 'xlsx', 'pptx']);
    final f = res.firstOrNull;
    if (f == null) return;
    // На Android файл может прийти через content://, тогда пути нет и читаем байты
    final path = f.path;
    await _upload(f.name, path: path, bytes: path == null ? await f.readAsBytes() : null);
  }

  Future<void> _upload(String name, {String? path, List<int>? bytes}) async {
    try {
      await ref.read(documentsProvider.notifier).upload(filename: name, path: path,
          bytes: bytes == null ? null : Uint8ListX.from(bytes), onProgress: (p) => setState(() => _progress = p));
    } catch (e) {
      if (mounted) showError(context, e);
    } finally {
      if (mounted) setState(() => _progress = null);
    }
  }

  Future<void> _ask(DocumentOut d) async {
    try {
      final chat = await ref.read(chatListProvider.notifier).create(title: d.title, documentIds: [d.id]);
      widget.onAsk(chat.id);
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final docs = ref.watch(documentsProvider);
    final content = Column(children: [
      if (_progress != null) LinearProgressIndicator(value: _progress!.fraction),
      Expanded(
        child: docs.when(
          loading: () => const LoadingView(),
          error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(documentsProvider)),
          data: (items) => items.isEmpty
              ? EmptyState(text: s.documentsEmpty, action: FilledButton.icon(onPressed: _pick,
                  icon: const Icon(Icons.upload_file), label: Text(s.upload)))
              : RefreshIndicator(
                  onRefresh: () => ref.refresh(documentsProvider.future),
                  child: ListView.separated(
                    padding: const EdgeInsets.all(Gaps.m),
                    itemCount: items.length,
                    separatorBuilder: (_, _) => const SizedBox(height: Gaps.s),
                    itemBuilder: (context, i) => _DocTile(doc: items[i], onAsk: () => _ask(items[i])),
                  ),
                ),
        ),
      ),
      Padding(
        padding: const EdgeInsets.all(Gaps.s),
        child: Text(s.docLimits, style: Theme.of(context).textTheme.bodySmall),
      ),
    ]);
    if (!widget.showAppBar) {
      return Stack(children: [
        content,
        Positioned(right: Gaps.m, bottom: Gaps.xl, child: FloatingActionButton.extended(
            onPressed: _pick, icon: const Icon(Icons.upload_file), label: Text(s.upload))),
      ]);
    }
    return Scaffold(
      appBar: AppBar(title: Text(s.documents)),
      body: content,
      floatingActionButton: FloatingActionButton.extended(onPressed: _pick, icon: const Icon(Icons.upload_file),
          label: Text(s.upload)),
    );
  }
}

extension Uint8ListX on List<int> {
  static Uint8List from(List<int> v) => v is Uint8List ? v : Uint8List.fromList(v);
}

class _DocTile extends ConsumerWidget {
  const _DocTile({required this.doc, required this.onAsk});

  final DocumentOut doc;
  final VoidCallback onAsk;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final processing = processingStatuses.contains(doc.status);
    final failed = doc.status == 'failed';
    final icon = switch (doc.kind) {
      'pdf' => Icons.picture_as_pdf_outlined,
      'xlsx' => Icons.table_chart_outlined,
      'pptx' => Icons.slideshow_outlined,
      _ => Icons.description_outlined,
    };
    final status = processing ? s.statusProcessing : (failed ? docFailure(s, doc.error) : s.statusReady);
    return Card(
      child: ListTile(
        leading: Icon(icon),
        title: Text(doc.title, maxLines: 2, overflow: TextOverflow.ellipsis),
        subtitle: Row(children: [
          if (processing) const Padding(padding: EdgeInsets.only(right: 6),
              child: SizedBox(width: 12, height: 12, child: CircularProgressIndicator(strokeWidth: 2))),
          Flexible(child: Text([status, if (doc.pages != null) s.pages(doc.pages!),
            '${(doc.sizeBytes / 1024 / 1024).toStringAsFixed(1)} МБ'].join(' · '))),
        ]),
        trailing: Row(mainAxisSize: MainAxisSize.min, children: [
          if (doc.status == 'ready') IconButton(icon: const Icon(Icons.question_answer_outlined), tooltip: s.askDocument,
              onPressed: onAsk),
          IconButton(
            icon: const Icon(Icons.delete_outline),
            tooltip: s.delete,
            onPressed: () async {
              if (await confirm(context, title: s.deleteDocument, body: s.deleteDocumentBody, action: s.delete)) {
                try {
                  await ref.read(documentsProvider.notifier).remove(doc.id);
                } catch (e) {
                  if (context.mounted) showError(context, e);
                }
              }
            },
          ),
        ]),
      ),
    );
  }
}

/// Фрагмент документа, на который сослался ассистент.
class SourceScreen extends ConsumerWidget {
  const SourceScreen({super.key, required this.documentId, required this.chunkId});

  final String documentId;
  final String chunkId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final chunk = ref.watch(chunkProvider((documentId, chunkId)));
    return Scaffold(
      appBar: AppBar(title: Text(s.sourceTitle)),
      body: chunk.when(
        loading: () => const LoadingView(),
        error: (e, _) => ErrorView(error: e),
        data: (c) => Readable(
          child: ListView(padding: const EdgeInsets.all(Gaps.m), children: [
            Text(c.title, style: Theme.of(context).textTheme.titleMedium),
            Text([if (c.page != null) s.page('${c.page}'), if (c.sheet != null) s.sheet(c.sheet!),
              if (c.section != null) c.section!].join(' · '), style: Theme.of(context).textTheme.bodySmall),
            const Divider(height: Gaps.l),
            if (c.prevText != null)
              Text(c.prevText!, style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
            Container(
              margin: const EdgeInsets.symmetric(vertical: Gaps.s),
              padding: const EdgeInsets.all(Gaps.m),
              color: Theme.of(context).colorScheme.secondaryContainer,
              child: SelectableText(c.text),
            ),
            if (c.nextText != null)
              Text(c.nextText!, style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant)),
          ]),
        ),
      ),
    );
  }
}
