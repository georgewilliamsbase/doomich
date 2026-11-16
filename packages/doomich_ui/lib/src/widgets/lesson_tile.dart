import 'package:doomich_api/doomich_api.dart';
import 'package:flutter/material.dart';

import '../strings.dart';

class LessonTile extends StatelessWidget {
  const LessonTile({super.key, required this.lesson, this.highlight = false, this.onTap, this.offsetMinutes});

  final LessonOut lesson;

  /// Смещение часового пояса вуза: время пары показывается по часам вуза
  final int? offsetMinutes;
  final bool highlight;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final cancelled = lesson.status == 'cancelled';
    final style = cancelled ? const TextStyle(decoration: TextDecoration.lineThrough) : null;
    final details = [
      kindText(s, lesson.kind),
      if (lesson.room != null) s.room(lesson.room!),
      if (lesson.teacher != null) lesson.teacher!,
      if (lesson.subgroup != null) '${s.subgroup} ${lesson.subgroup}',
    ].join(' · ');
    return Card(
      color: highlight ? scheme.secondaryContainer : null,
      child: ListTile(
        onTap: onTap,
        leading: SizedBox(
          width: 52,
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            Text(hhmm(lesson.startsAt, offsetMinutes), style: const TextStyle(fontWeight: FontWeight.w600)),
            Text(hhmm(lesson.endsAt, offsetMinutes), style: Theme.of(context).textTheme.bodySmall),
          ]),
        ),
        title: Text(lesson.subject, style: style),
        subtitle: Text(cancelled ? '${s.cancelled} · $details' : details),
        trailing: lesson.note == null ? null : Tooltip(message: lesson.note!, child: const Icon(Icons.info_outline)),
      ),
    );
  }
}
