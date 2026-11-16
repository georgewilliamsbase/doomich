import 'dart:math';
import 'dart:typed_data';

import 'package:doomich_api/doomich_api.dart';
import 'package:doomich_core/doomich_core.dart';
import 'package:drift/drift.dart' hide isNull;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

LessonOut lesson(String id, DateTime start, {String status = 'scheduled'}) => LessonOut(
    id: id, groupId: 'g', subject: 'Предмет $id', kind: 'lecture', startsAt: start,
    endsAt: start.add(const Duration(minutes: 90)), status: status);

void main() {
  test('ключ преподавателя совпадает с серверным', () {
    // Значения посчитаны функцией teacher_key из services/api (schedule/sync.py)
    expect(teacherKey('demo', 'Иванова Мария Петровна'), '79faf865f1589942329fc691');
    expect(teacherKey('demo', 'Сидоров П. П.'), 'de4f19880c663f5682de5c87');
    expect(teacherKey('demo', 'сидоров п.п.'), teacherKey('demo', 'Сидоров П. П.'));
  });

  test('ссылка-приглашение и ввод кода руками', () {
    final l = InviteLink.parse('doomich://invite/abcd-efgh?server=https://doomich.example.ru')!;
    expect(l.code, 'ABCD-EFGH');
    expect(l.server, 'https://doomich.example.ru');
    expect(InviteLink.parse('doomich://invite/ABCDEFGH?server=http://evil.example')!.server, isNull);
    // Кириллица вместо похожих латинских букв
    expect(InviteLink.parse('код: АВСЕ КМНР')?.code, isNull);
    expect(InviteLink.parse('АВСЕ-КМНР')!.code, 'ABCE-KMHP');
    expect(InviteLink.parse('просто текст'), isNull);
  });

  test('псевдонимы и правила логина', () {
    final gen = PseudonymGenerator(Random(1));
    final s = gen.suggestions(count: 5);
    expect(s.toSet().length, 5);
    for (final p in s) {
      expect(LoginRules.isValid(p), isTrue, reason: p);
      expect(LoginRules.looksLikeName(p), isFalse, reason: p);
    }
    expect(LoginRules.looksLikeName('ИванПетров'), isTrue);
    expect(LoginRules.looksLikeName('ПетровИван'), isTrue);
    expect(LoginRules.looksLikeName('ЗоркийФилин42'), isFalse);
    expect(LoginRules.warning('ivan@mail.ru'), 'looks_like_email');
    expect(LoginRules.isValid('ab'), isFalse);
  });

  test('оценка пароля', () {
    expect(passwordScore('short'), 0);
    expect(passwordScore('1234567890'), 0);
    expect(passwordScore('Kosmos-Galaktika-42'), greaterThanOrEqualTo(3));
    expect(passwordScore('енотенот123456', login: 'енот'), 1);
  });

  test('детектор речи останавливается после паузы', () {
    final vad = EnergyVad(silenceMs: 300, minSpeechMs: 200);
    Uint8List chunk(double amp) {
      final b = ByteData(3200);
      for (var i = 0; i < 1600; i++) {
        b.setInt16(i * 2, (amp * 32767 * sin(i / 5)).toInt(), Endian.little);
      }
      return b.buffer.asUint8List();
    }

    expect(vad.feed(chunk(0)), isFalse); // тишина до речи не считается
    expect(vad.feed(chunk(0.5)), isFalse);
    expect(vad.feed(chunk(0.5)), isFalse);
    expect(vad.feed(chunk(0)), isFalse);
    expect(vad.feed(chunk(0)), isFalse);
    expect(vad.feed(chunk(0)), isTrue);
  });

  test('настройки сохраняются в JSON и обратно', () {
    const s = AppSettings(themeMode: ThemeMode.dark, localeCode: 'en', deviceGroupId: 'g1', speechRate: 1.25);
    final back = AppSettings.fromJson(s.toJson());
    expect(back.themeMode, ThemeMode.dark);
    expect(back.locale, const Locale('en'));
    expect(back.deviceGroupId, 'g1');
    expect(back.speechRate, 1.25);
    expect(back.copyWith(deviceGroupId: null).deviceGroupId, isNull);
    expect(back.copyWith(readAloud: true).deviceGroupId, 'g1');
  });

  test('текущая и следующая пара', () {
    final base = DateTime(2027, 2, 8, 8, 30);
    final week = WeekSchedule(from: base, to: base, lessons: [
      lesson('1', base),
      lesson('2', base.add(const Duration(hours: 2)), status: 'cancelled'),
      lesson('3', base.add(const Duration(hours: 4))),
    ]);
    final (cur, next) = week.nowNext(base.add(const Duration(minutes: 30)));
    expect(cur!.id, '1');
    expect(next!.id, '3');
    expect(week.forDay(DateTime(2027, 2, 8)).length, 3);
    expect(mondayOf(DateTime(2027, 2, 11)), DateTime(2027, 2, 8));
  });

  test('локальная база: кэш расписания', () async {
    final db = AppDb(NativeDatabase.memory());
    await db.into(db.cachedLessons).insert(CachedLessonsCompanion.insert(
        id: 'l1', scope: 'g:1:', startsAt: DateTime(2027, 2, 8, 9), endsAt: DateTime(2027, 2, 8, 10),
        subject: 'Физика', kind: 'lab', status: 'scheduled', room: const Value('112')));
    final rows = await db.select(db.cachedLessons).get();
    expect(rows.single.room, '112');
    await db.wipe();
    expect(await db.select(db.cachedLessons).get(), isEmpty);
    await db.close();
  });
}
