import 'package:doomich_api/doomich_api.dart';
import 'package:drift/drift.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/app_db.dart';
import 'app.dart';
import 'auth.dart';

/// Чьё расписание показываем: группа (с сервера или только с устройства) или преподаватель.
class ScheduleScope {
  const ScheduleScope({this.groupId, this.groupCode, this.subgroup, this.teacherKey, this.teacherName});

  final String? groupId;
  final String? groupCode;
  final String? subgroup;
  final String? teacherKey;
  final String? teacherName;

  bool get isTeacher => teacherKey != null;

  String get key => isTeacher ? 't:$teacherKey' : 'g:$groupId:${subgroup ?? ''}';

  String get title => isTeacher ? (teacherName ?? '') : (groupCode ?? '');
}

final scheduleScopeProvider = Provider<ScheduleScope?>((ref) {
  final s = ref.watch(settingsProvider);
  final me = ref.watch(meProvider);
  if (s.teacherKey != null && (me?.role == 'teacher')) {
    return ScheduleScope(teacherKey: s.teacherKey, teacherName: s.teacherName);
  }
  if (s.deviceGroupId != null) {
    return ScheduleScope(groupId: s.deviceGroupId, groupCode: s.deviceGroupCode, subgroup: s.deviceSubgroup);
  }
  final g = me?.group;
  if (g != null) return ScheduleScope(groupId: g.id, groupCode: g.code, subgroup: me?.subgroup);
  return null;
});

/// Время на часах вуза: момент в UTC плюс смещение часового пояса вуза.
/// Результат хранится как UTC-дата, у которой поля часов и минут совпадают с часами вуза.
DateTime campusTime(DateTime t, int offsetMinutes) => t.toUtc().add(Duration(minutes: offsetMinutes));

class WeekSchedule {
  const WeekSchedule({required this.lessons, required this.from, required this.to, this.fetchedAt, this.offline = false,
      this.version, this.offsetMinutes = 180});

  final List<LessonOut> lessons;
  final DateTime from;
  final DateTime to;
  final DateTime? fetchedAt;
  final bool offline;
  final String? version;

  /// Смещение часового пояса вуза в минутах
  final int offsetMinutes;

  DateTime campus(DateTime t) => campusTime(t, offsetMinutes);

  List<LessonOut> forDay(DateTime day) => lessons
      .where((l) {
        final d = campus(l.startsAt);
        return d.year == day.year && d.month == day.month && d.day == day.day;
      })
      .toList();

  /// Текущая и следующая пара относительно [now].
  (LessonOut?, LessonOut?) nowNext(DateTime now) {
    LessonOut? current;
    LessonOut? next;
    for (final l in lessons) {
      if (l.status == 'cancelled') continue;
      final s = l.startsAt.toLocal();
      final e = l.endsAt.toLocal();
      if (!s.isAfter(now) && e.isAfter(now)) current = l;
      if (s.isAfter(now) && (next == null || s.isBefore(next.startsAt.toLocal()))) next = l;
    }
    return (current, next);
  }
}

DateTime mondayOf(DateTime d) {
  final day = DateTime(d.year, d.month, d.day);
  return day.subtract(Duration(days: day.weekday - 1));
}

/// Расписание на две недели начиная с понедельника [weekStart]. Без сети берётся последняя копия.
class ScheduleController extends AsyncNotifier<WeekSchedule> {
  ScheduleController(this.weekStart);

  final DateTime weekStart;

  @override
  Future<WeekSchedule> build() async {
    final scope = ref.watch(scheduleScopeProvider);
    final from = mondayOf(weekStart);
    final to = from.add(const Duration(days: 13));
    if (scope == null) return WeekSchedule(lessons: const [], from: from, to: to);
    final api = ref.read(apiClientProvider);
    final db = ref.read(dbProvider);
    try {
      final out = await api.schedule(groupId: scope.isTeacher ? null : scope.groupId, subgroup: scope.subgroup,
          teacherKey: scope.teacherKey, from: from, to: to);
      try {
        await _save(db, scope, out, from, to);
      } catch (_) {
        // Кэш вспомогательный: если запись не удалась, всё равно показываем свежие данные
      }
      return WeekSchedule(lessons: out.lessons, from: from, to: to, fetchedAt: DateTime.now(), version: out.version,
          offsetMinutes: out.utcOffsetMinutes);
    } on ApiException catch (e) {
      if (!e.isNetwork) rethrow;
      return _load(db, scope, from, to);
    }
  }

  Future<void> _save(AppDb db, ScheduleScope scope, ScheduleOut out, DateTime from, DateTime to) async {
    await db.transaction(() async {
      await (db.delete(db.cachedLessons)
            ..where((t) => t.scope.equals(scope.key) & t.startsAt.isBetweenValues(from, to.add(const Duration(days: 1)))))
          .go();
      for (final l in out.lessons) {
        await db.into(db.cachedLessons).insertOnConflictUpdate(CachedLessonsCompanion.insert(
              id: l.id, scope: scope.key, startsAt: l.startsAt, endsAt: l.endsAt, subject: l.subject, kind: l.kind,
              status: l.status, room: Value(l.room), campusRoomId: Value(l.campusRoomId), teacher: Value(l.teacher),
              subgroup: Value(l.subgroup), note: Value(l.note)));
      }
      await db.into(db.scheduleMeta).insertOnConflictUpdate(ScheduleMetaCompanion.insert(
          scope: scope.key, fetchedAt: DateTime.now(), dateFrom: from, dateTo: to, version: out.version,
          groupCode: Value(out.group?.code), utcOffset: Value(out.utcOffsetMinutes)));
    });
  }

  Future<WeekSchedule> _load(AppDb db, ScheduleScope scope, DateTime from, DateTime to) async {
    final rows = await (db.select(db.cachedLessons)
          ..where((t) => t.scope.equals(scope.key) & t.startsAt.isBetweenValues(from, to.add(const Duration(days: 1))))
          ..orderBy([(t) => OrderingTerm.asc(t.startsAt)]))
        .get();
    final meta = await (db.select(db.scheduleMeta)..where((t) => t.scope.equals(scope.key))).getSingleOrNull();
    return WeekSchedule(
      lessons: rows
          .map((r) => LessonOut(id: r.id, groupId: scope.groupId ?? '', subgroup: r.subgroup, subject: r.subject,
              kind: r.kind, startsAt: r.startsAt, endsAt: r.endsAt, room: r.room, campusRoomId: r.campusRoomId,
              teacher: r.teacher, teacherKey: scope.teacherKey, note: r.note, status: r.status))
          .toList(),
      from: from,
      to: to,
      fetchedAt: meta?.fetchedAt,
      offline: true,
      offsetMinutes: meta?.utcOffset ?? 180,
    );
  }
}

final scheduleProvider =
    AsyncNotifierProvider.family<ScheduleController, WeekSchedule, DateTime>(ScheduleController.new);

final groupSearchProvider = FutureProvider.autoDispose.family<List<GroupOut>, String>((ref, q) async {
  return ref.read(apiClientProvider).groups(query: q.isEmpty ? null : q, limit: 100);
});
