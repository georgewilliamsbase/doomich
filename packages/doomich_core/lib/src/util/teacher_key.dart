import 'dart:convert';

import 'package:crypto/crypto.dart';

/// Ключ преподавателя для его расписания. Считается на устройстве из имени,
/// которое ввёл сам преподаватель. Так сервер не хранит связь "аккаунт = преподаватель".
/// Формула совпадает с schedule/sync.py: `sha256("<slug вуза>:<нормализованное имя>")[:24]`.
String teacherKey(String tenantSlug, String name) {
  final normalized = name.toLowerCase().replaceAll('ё', 'е').replaceAll('.', ' ').split(RegExp(r'\s+'))
      .where((p) => p.isNotEmpty).join(' ');
  return sha256.convert(utf8.encode('$tenantSlug:$normalized')).toString().substring(0, 24);
}
