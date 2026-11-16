// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_db.dart';

// ignore_for_file: type=lint
class $CachedLessonsTable extends CachedLessons
    with TableInfo<$CachedLessonsTable, CachedLesson> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedLessonsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _scopeMeta = const VerificationMeta('scope');
  @override
  late final GeneratedColumn<String> scope = GeneratedColumn<String>(
    'scope',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _startsAtMeta = const VerificationMeta(
    'startsAt',
  );
  @override
  late final GeneratedColumn<DateTime> startsAt = GeneratedColumn<DateTime>(
    'starts_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _endsAtMeta = const VerificationMeta('endsAt');
  @override
  late final GeneratedColumn<DateTime> endsAt = GeneratedColumn<DateTime>(
    'ends_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _subjectMeta = const VerificationMeta(
    'subject',
  );
  @override
  late final GeneratedColumn<String> subject = GeneratedColumn<String>(
    'subject',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _kindMeta = const VerificationMeta('kind');
  @override
  late final GeneratedColumn<String> kind = GeneratedColumn<String>(
    'kind',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _roomMeta = const VerificationMeta('room');
  @override
  late final GeneratedColumn<String> room = GeneratedColumn<String>(
    'room',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _campusRoomIdMeta = const VerificationMeta(
    'campusRoomId',
  );
  @override
  late final GeneratedColumn<String> campusRoomId = GeneratedColumn<String>(
    'campus_room_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _teacherMeta = const VerificationMeta(
    'teacher',
  );
  @override
  late final GeneratedColumn<String> teacher = GeneratedColumn<String>(
    'teacher',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _subgroupMeta = const VerificationMeta(
    'subgroup',
  );
  @override
  late final GeneratedColumn<String> subgroup = GeneratedColumn<String>(
    'subgroup',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _noteMeta = const VerificationMeta('note');
  @override
  late final GeneratedColumn<String> note = GeneratedColumn<String>(
    'note',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    scope,
    startsAt,
    endsAt,
    subject,
    kind,
    room,
    campusRoomId,
    teacher,
    subgroup,
    note,
    status,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_lessons';
  @override
  VerificationContext validateIntegrity(
    Insertable<CachedLesson> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('scope')) {
      context.handle(
        _scopeMeta,
        scope.isAcceptableOrUnknown(data['scope']!, _scopeMeta),
      );
    } else if (isInserting) {
      context.missing(_scopeMeta);
    }
    if (data.containsKey('starts_at')) {
      context.handle(
        _startsAtMeta,
        startsAt.isAcceptableOrUnknown(data['starts_at']!, _startsAtMeta),
      );
    } else if (isInserting) {
      context.missing(_startsAtMeta);
    }
    if (data.containsKey('ends_at')) {
      context.handle(
        _endsAtMeta,
        endsAt.isAcceptableOrUnknown(data['ends_at']!, _endsAtMeta),
      );
    } else if (isInserting) {
      context.missing(_endsAtMeta);
    }
    if (data.containsKey('subject')) {
      context.handle(
        _subjectMeta,
        subject.isAcceptableOrUnknown(data['subject']!, _subjectMeta),
      );
    } else if (isInserting) {
      context.missing(_subjectMeta);
    }
    if (data.containsKey('kind')) {
      context.handle(
        _kindMeta,
        kind.isAcceptableOrUnknown(data['kind']!, _kindMeta),
      );
    } else if (isInserting) {
      context.missing(_kindMeta);
    }
    if (data.containsKey('room')) {
      context.handle(
        _roomMeta,
        room.isAcceptableOrUnknown(data['room']!, _roomMeta),
      );
    }
    if (data.containsKey('campus_room_id')) {
      context.handle(
        _campusRoomIdMeta,
        campusRoomId.isAcceptableOrUnknown(
          data['campus_room_id']!,
          _campusRoomIdMeta,
        ),
      );
    }
    if (data.containsKey('teacher')) {
      context.handle(
        _teacherMeta,
        teacher.isAcceptableOrUnknown(data['teacher']!, _teacherMeta),
      );
    }
    if (data.containsKey('subgroup')) {
      context.handle(
        _subgroupMeta,
        subgroup.isAcceptableOrUnknown(data['subgroup']!, _subgroupMeta),
      );
    }
    if (data.containsKey('note')) {
      context.handle(
        _noteMeta,
        note.isAcceptableOrUnknown(data['note']!, _noteMeta),
      );
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id, scope};
  @override
  CachedLesson map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedLesson(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      scope: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}scope'],
      )!,
      startsAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}starts_at'],
      )!,
      endsAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}ends_at'],
      )!,
      subject: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}subject'],
      )!,
      kind: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}kind'],
      )!,
      room: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}room'],
      ),
      campusRoomId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}campus_room_id'],
      ),
      teacher: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}teacher'],
      ),
      subgroup: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}subgroup'],
      ),
      note: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}note'],
      ),
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      )!,
    );
  }

  @override
  $CachedLessonsTable createAlias(String alias) {
    return $CachedLessonsTable(attachedDatabase, alias);
  }
}

class CachedLesson extends DataClass implements Insertable<CachedLesson> {
  final String id;

  /// Ключ выборки: `g:<id группы>:<подгруппа>` или `t:<ключ преподавателя>`
  final String scope;
  final DateTime startsAt;
  final DateTime endsAt;
  final String subject;
  final String kind;
  final String? room;
  final String? campusRoomId;
  final String? teacher;
  final String? subgroup;
  final String? note;
  final String status;
  const CachedLesson({
    required this.id,
    required this.scope,
    required this.startsAt,
    required this.endsAt,
    required this.subject,
    required this.kind,
    this.room,
    this.campusRoomId,
    this.teacher,
    this.subgroup,
    this.note,
    required this.status,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['scope'] = Variable<String>(scope);
    map['starts_at'] = Variable<DateTime>(startsAt);
    map['ends_at'] = Variable<DateTime>(endsAt);
    map['subject'] = Variable<String>(subject);
    map['kind'] = Variable<String>(kind);
    if (!nullToAbsent || room != null) {
      map['room'] = Variable<String>(room);
    }
    if (!nullToAbsent || campusRoomId != null) {
      map['campus_room_id'] = Variable<String>(campusRoomId);
    }
    if (!nullToAbsent || teacher != null) {
      map['teacher'] = Variable<String>(teacher);
    }
    if (!nullToAbsent || subgroup != null) {
      map['subgroup'] = Variable<String>(subgroup);
    }
    if (!nullToAbsent || note != null) {
      map['note'] = Variable<String>(note);
    }
    map['status'] = Variable<String>(status);
    return map;
  }

  CachedLessonsCompanion toCompanion(bool nullToAbsent) {
    return CachedLessonsCompanion(
      id: Value(id),
      scope: Value(scope),
      startsAt: Value(startsAt),
      endsAt: Value(endsAt),
      subject: Value(subject),
      kind: Value(kind),
      room: room == null && nullToAbsent ? const Value.absent() : Value(room),
      campusRoomId: campusRoomId == null && nullToAbsent
          ? const Value.absent()
          : Value(campusRoomId),
      teacher: teacher == null && nullToAbsent
          ? const Value.absent()
          : Value(teacher),
      subgroup: subgroup == null && nullToAbsent
          ? const Value.absent()
          : Value(subgroup),
      note: note == null && nullToAbsent ? const Value.absent() : Value(note),
      status: Value(status),
    );
  }

  factory CachedLesson.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedLesson(
      id: serializer.fromJson<String>(json['id']),
      scope: serializer.fromJson<String>(json['scope']),
      startsAt: serializer.fromJson<DateTime>(json['startsAt']),
      endsAt: serializer.fromJson<DateTime>(json['endsAt']),
      subject: serializer.fromJson<String>(json['subject']),
      kind: serializer.fromJson<String>(json['kind']),
      room: serializer.fromJson<String?>(json['room']),
      campusRoomId: serializer.fromJson<String?>(json['campusRoomId']),
      teacher: serializer.fromJson<String?>(json['teacher']),
      subgroup: serializer.fromJson<String?>(json['subgroup']),
      note: serializer.fromJson<String?>(json['note']),
      status: serializer.fromJson<String>(json['status']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'scope': serializer.toJson<String>(scope),
      'startsAt': serializer.toJson<DateTime>(startsAt),
      'endsAt': serializer.toJson<DateTime>(endsAt),
      'subject': serializer.toJson<String>(subject),
      'kind': serializer.toJson<String>(kind),
      'room': serializer.toJson<String?>(room),
      'campusRoomId': serializer.toJson<String?>(campusRoomId),
      'teacher': serializer.toJson<String?>(teacher),
      'subgroup': serializer.toJson<String?>(subgroup),
      'note': serializer.toJson<String?>(note),
      'status': serializer.toJson<String>(status),
    };
  }

  CachedLesson copyWith({
    String? id,
    String? scope,
    DateTime? startsAt,
    DateTime? endsAt,
    String? subject,
    String? kind,
    Value<String?> room = const Value.absent(),
    Value<String?> campusRoomId = const Value.absent(),
    Value<String?> teacher = const Value.absent(),
    Value<String?> subgroup = const Value.absent(),
    Value<String?> note = const Value.absent(),
    String? status,
  }) => CachedLesson(
    id: id ?? this.id,
    scope: scope ?? this.scope,
    startsAt: startsAt ?? this.startsAt,
    endsAt: endsAt ?? this.endsAt,
    subject: subject ?? this.subject,
    kind: kind ?? this.kind,
    room: room.present ? room.value : this.room,
    campusRoomId: campusRoomId.present ? campusRoomId.value : this.campusRoomId,
    teacher: teacher.present ? teacher.value : this.teacher,
    subgroup: subgroup.present ? subgroup.value : this.subgroup,
    note: note.present ? note.value : this.note,
    status: status ?? this.status,
  );
  CachedLesson copyWithCompanion(CachedLessonsCompanion data) {
    return CachedLesson(
      id: data.id.present ? data.id.value : this.id,
      scope: data.scope.present ? data.scope.value : this.scope,
      startsAt: data.startsAt.present ? data.startsAt.value : this.startsAt,
      endsAt: data.endsAt.present ? data.endsAt.value : this.endsAt,
      subject: data.subject.present ? data.subject.value : this.subject,
      kind: data.kind.present ? data.kind.value : this.kind,
      room: data.room.present ? data.room.value : this.room,
      campusRoomId: data.campusRoomId.present
          ? data.campusRoomId.value
          : this.campusRoomId,
      teacher: data.teacher.present ? data.teacher.value : this.teacher,
      subgroup: data.subgroup.present ? data.subgroup.value : this.subgroup,
      note: data.note.present ? data.note.value : this.note,
      status: data.status.present ? data.status.value : this.status,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedLesson(')
          ..write('id: $id, ')
          ..write('scope: $scope, ')
          ..write('startsAt: $startsAt, ')
          ..write('endsAt: $endsAt, ')
          ..write('subject: $subject, ')
          ..write('kind: $kind, ')
          ..write('room: $room, ')
          ..write('campusRoomId: $campusRoomId, ')
          ..write('teacher: $teacher, ')
          ..write('subgroup: $subgroup, ')
          ..write('note: $note, ')
          ..write('status: $status')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    scope,
    startsAt,
    endsAt,
    subject,
    kind,
    room,
    campusRoomId,
    teacher,
    subgroup,
    note,
    status,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedLesson &&
          other.id == this.id &&
          other.scope == this.scope &&
          other.startsAt == this.startsAt &&
          other.endsAt == this.endsAt &&
          other.subject == this.subject &&
          other.kind == this.kind &&
          other.room == this.room &&
          other.campusRoomId == this.campusRoomId &&
          other.teacher == this.teacher &&
          other.subgroup == this.subgroup &&
          other.note == this.note &&
          other.status == this.status);
}

class CachedLessonsCompanion extends UpdateCompanion<CachedLesson> {
  final Value<String> id;
  final Value<String> scope;
  final Value<DateTime> startsAt;
  final Value<DateTime> endsAt;
  final Value<String> subject;
  final Value<String> kind;
  final Value<String?> room;
  final Value<String?> campusRoomId;
  final Value<String?> teacher;
  final Value<String?> subgroup;
  final Value<String?> note;
  final Value<String> status;
  final Value<int> rowid;
  const CachedLessonsCompanion({
    this.id = const Value.absent(),
    this.scope = const Value.absent(),
    this.startsAt = const Value.absent(),
    this.endsAt = const Value.absent(),
    this.subject = const Value.absent(),
    this.kind = const Value.absent(),
    this.room = const Value.absent(),
    this.campusRoomId = const Value.absent(),
    this.teacher = const Value.absent(),
    this.subgroup = const Value.absent(),
    this.note = const Value.absent(),
    this.status = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedLessonsCompanion.insert({
    required String id,
    required String scope,
    required DateTime startsAt,
    required DateTime endsAt,
    required String subject,
    required String kind,
    this.room = const Value.absent(),
    this.campusRoomId = const Value.absent(),
    this.teacher = const Value.absent(),
    this.subgroup = const Value.absent(),
    this.note = const Value.absent(),
    required String status,
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       scope = Value(scope),
       startsAt = Value(startsAt),
       endsAt = Value(endsAt),
       subject = Value(subject),
       kind = Value(kind),
       status = Value(status);
  static Insertable<CachedLesson> custom({
    Expression<String>? id,
    Expression<String>? scope,
    Expression<DateTime>? startsAt,
    Expression<DateTime>? endsAt,
    Expression<String>? subject,
    Expression<String>? kind,
    Expression<String>? room,
    Expression<String>? campusRoomId,
    Expression<String>? teacher,
    Expression<String>? subgroup,
    Expression<String>? note,
    Expression<String>? status,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (scope != null) 'scope': scope,
      if (startsAt != null) 'starts_at': startsAt,
      if (endsAt != null) 'ends_at': endsAt,
      if (subject != null) 'subject': subject,
      if (kind != null) 'kind': kind,
      if (room != null) 'room': room,
      if (campusRoomId != null) 'campus_room_id': campusRoomId,
      if (teacher != null) 'teacher': teacher,
      if (subgroup != null) 'subgroup': subgroup,
      if (note != null) 'note': note,
      if (status != null) 'status': status,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedLessonsCompanion copyWith({
    Value<String>? id,
    Value<String>? scope,
    Value<DateTime>? startsAt,
    Value<DateTime>? endsAt,
    Value<String>? subject,
    Value<String>? kind,
    Value<String?>? room,
    Value<String?>? campusRoomId,
    Value<String?>? teacher,
    Value<String?>? subgroup,
    Value<String?>? note,
    Value<String>? status,
    Value<int>? rowid,
  }) {
    return CachedLessonsCompanion(
      id: id ?? this.id,
      scope: scope ?? this.scope,
      startsAt: startsAt ?? this.startsAt,
      endsAt: endsAt ?? this.endsAt,
      subject: subject ?? this.subject,
      kind: kind ?? this.kind,
      room: room ?? this.room,
      campusRoomId: campusRoomId ?? this.campusRoomId,
      teacher: teacher ?? this.teacher,
      subgroup: subgroup ?? this.subgroup,
      note: note ?? this.note,
      status: status ?? this.status,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (scope.present) {
      map['scope'] = Variable<String>(scope.value);
    }
    if (startsAt.present) {
      map['starts_at'] = Variable<DateTime>(startsAt.value);
    }
    if (endsAt.present) {
      map['ends_at'] = Variable<DateTime>(endsAt.value);
    }
    if (subject.present) {
      map['subject'] = Variable<String>(subject.value);
    }
    if (kind.present) {
      map['kind'] = Variable<String>(kind.value);
    }
    if (room.present) {
      map['room'] = Variable<String>(room.value);
    }
    if (campusRoomId.present) {
      map['campus_room_id'] = Variable<String>(campusRoomId.value);
    }
    if (teacher.present) {
      map['teacher'] = Variable<String>(teacher.value);
    }
    if (subgroup.present) {
      map['subgroup'] = Variable<String>(subgroup.value);
    }
    if (note.present) {
      map['note'] = Variable<String>(note.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedLessonsCompanion(')
          ..write('id: $id, ')
          ..write('scope: $scope, ')
          ..write('startsAt: $startsAt, ')
          ..write('endsAt: $endsAt, ')
          ..write('subject: $subject, ')
          ..write('kind: $kind, ')
          ..write('room: $room, ')
          ..write('campusRoomId: $campusRoomId, ')
          ..write('teacher: $teacher, ')
          ..write('subgroup: $subgroup, ')
          ..write('note: $note, ')
          ..write('status: $status, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $ScheduleMetaTable extends ScheduleMeta
    with TableInfo<$ScheduleMetaTable, ScheduleMetaData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ScheduleMetaTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _scopeMeta = const VerificationMeta('scope');
  @override
  late final GeneratedColumn<String> scope = GeneratedColumn<String>(
    'scope',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _fetchedAtMeta = const VerificationMeta(
    'fetchedAt',
  );
  @override
  late final GeneratedColumn<DateTime> fetchedAt = GeneratedColumn<DateTime>(
    'fetched_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _dateFromMeta = const VerificationMeta(
    'dateFrom',
  );
  @override
  late final GeneratedColumn<DateTime> dateFrom = GeneratedColumn<DateTime>(
    'date_from',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _dateToMeta = const VerificationMeta('dateTo');
  @override
  late final GeneratedColumn<DateTime> dateTo = GeneratedColumn<DateTime>(
    'date_to',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _versionMeta = const VerificationMeta(
    'version',
  );
  @override
  late final GeneratedColumn<String> version = GeneratedColumn<String>(
    'version',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _groupCodeMeta = const VerificationMeta(
    'groupCode',
  );
  @override
  late final GeneratedColumn<String> groupCode = GeneratedColumn<String>(
    'group_code',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _utcOffsetMeta = const VerificationMeta(
    'utcOffset',
  );
  @override
  late final GeneratedColumn<int> utcOffset = GeneratedColumn<int>(
    'utc_offset',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(180),
  );
  @override
  List<GeneratedColumn> get $columns => [
    scope,
    fetchedAt,
    dateFrom,
    dateTo,
    version,
    groupCode,
    utcOffset,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'schedule_meta';
  @override
  VerificationContext validateIntegrity(
    Insertable<ScheduleMetaData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('scope')) {
      context.handle(
        _scopeMeta,
        scope.isAcceptableOrUnknown(data['scope']!, _scopeMeta),
      );
    } else if (isInserting) {
      context.missing(_scopeMeta);
    }
    if (data.containsKey('fetched_at')) {
      context.handle(
        _fetchedAtMeta,
        fetchedAt.isAcceptableOrUnknown(data['fetched_at']!, _fetchedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_fetchedAtMeta);
    }
    if (data.containsKey('date_from')) {
      context.handle(
        _dateFromMeta,
        dateFrom.isAcceptableOrUnknown(data['date_from']!, _dateFromMeta),
      );
    } else if (isInserting) {
      context.missing(_dateFromMeta);
    }
    if (data.containsKey('date_to')) {
      context.handle(
        _dateToMeta,
        dateTo.isAcceptableOrUnknown(data['date_to']!, _dateToMeta),
      );
    } else if (isInserting) {
      context.missing(_dateToMeta);
    }
    if (data.containsKey('version')) {
      context.handle(
        _versionMeta,
        version.isAcceptableOrUnknown(data['version']!, _versionMeta),
      );
    } else if (isInserting) {
      context.missing(_versionMeta);
    }
    if (data.containsKey('group_code')) {
      context.handle(
        _groupCodeMeta,
        groupCode.isAcceptableOrUnknown(data['group_code']!, _groupCodeMeta),
      );
    }
    if (data.containsKey('utc_offset')) {
      context.handle(
        _utcOffsetMeta,
        utcOffset.isAcceptableOrUnknown(data['utc_offset']!, _utcOffsetMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {scope};
  @override
  ScheduleMetaData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return ScheduleMetaData(
      scope: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}scope'],
      )!,
      fetchedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}fetched_at'],
      )!,
      dateFrom: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}date_from'],
      )!,
      dateTo: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}date_to'],
      )!,
      version: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}version'],
      )!,
      groupCode: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}group_code'],
      ),
      utcOffset: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}utc_offset'],
      )!,
    );
  }

  @override
  $ScheduleMetaTable createAlias(String alias) {
    return $ScheduleMetaTable(attachedDatabase, alias);
  }
}

class ScheduleMetaData extends DataClass
    implements Insertable<ScheduleMetaData> {
  final String scope;
  final DateTime fetchedAt;
  final DateTime dateFrom;
  final DateTime dateTo;
  final String version;
  final String? groupCode;

  /// Смещение часового пояса вуза в минутах: расписание показывается по времени вуза
  final int utcOffset;
  const ScheduleMetaData({
    required this.scope,
    required this.fetchedAt,
    required this.dateFrom,
    required this.dateTo,
    required this.version,
    this.groupCode,
    required this.utcOffset,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['scope'] = Variable<String>(scope);
    map['fetched_at'] = Variable<DateTime>(fetchedAt);
    map['date_from'] = Variable<DateTime>(dateFrom);
    map['date_to'] = Variable<DateTime>(dateTo);
    map['version'] = Variable<String>(version);
    if (!nullToAbsent || groupCode != null) {
      map['group_code'] = Variable<String>(groupCode);
    }
    map['utc_offset'] = Variable<int>(utcOffset);
    return map;
  }

  ScheduleMetaCompanion toCompanion(bool nullToAbsent) {
    return ScheduleMetaCompanion(
      scope: Value(scope),
      fetchedAt: Value(fetchedAt),
      dateFrom: Value(dateFrom),
      dateTo: Value(dateTo),
      version: Value(version),
      groupCode: groupCode == null && nullToAbsent
          ? const Value.absent()
          : Value(groupCode),
      utcOffset: Value(utcOffset),
    );
  }

  factory ScheduleMetaData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return ScheduleMetaData(
      scope: serializer.fromJson<String>(json['scope']),
      fetchedAt: serializer.fromJson<DateTime>(json['fetchedAt']),
      dateFrom: serializer.fromJson<DateTime>(json['dateFrom']),
      dateTo: serializer.fromJson<DateTime>(json['dateTo']),
      version: serializer.fromJson<String>(json['version']),
      groupCode: serializer.fromJson<String?>(json['groupCode']),
      utcOffset: serializer.fromJson<int>(json['utcOffset']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'scope': serializer.toJson<String>(scope),
      'fetchedAt': serializer.toJson<DateTime>(fetchedAt),
      'dateFrom': serializer.toJson<DateTime>(dateFrom),
      'dateTo': serializer.toJson<DateTime>(dateTo),
      'version': serializer.toJson<String>(version),
      'groupCode': serializer.toJson<String?>(groupCode),
      'utcOffset': serializer.toJson<int>(utcOffset),
    };
  }

  ScheduleMetaData copyWith({
    String? scope,
    DateTime? fetchedAt,
    DateTime? dateFrom,
    DateTime? dateTo,
    String? version,
    Value<String?> groupCode = const Value.absent(),
    int? utcOffset,
  }) => ScheduleMetaData(
    scope: scope ?? this.scope,
    fetchedAt: fetchedAt ?? this.fetchedAt,
    dateFrom: dateFrom ?? this.dateFrom,
    dateTo: dateTo ?? this.dateTo,
    version: version ?? this.version,
    groupCode: groupCode.present ? groupCode.value : this.groupCode,
    utcOffset: utcOffset ?? this.utcOffset,
  );
  ScheduleMetaData copyWithCompanion(ScheduleMetaCompanion data) {
    return ScheduleMetaData(
      scope: data.scope.present ? data.scope.value : this.scope,
      fetchedAt: data.fetchedAt.present ? data.fetchedAt.value : this.fetchedAt,
      dateFrom: data.dateFrom.present ? data.dateFrom.value : this.dateFrom,
      dateTo: data.dateTo.present ? data.dateTo.value : this.dateTo,
      version: data.version.present ? data.version.value : this.version,
      groupCode: data.groupCode.present ? data.groupCode.value : this.groupCode,
      utcOffset: data.utcOffset.present ? data.utcOffset.value : this.utcOffset,
    );
  }

  @override
  String toString() {
    return (StringBuffer('ScheduleMetaData(')
          ..write('scope: $scope, ')
          ..write('fetchedAt: $fetchedAt, ')
          ..write('dateFrom: $dateFrom, ')
          ..write('dateTo: $dateTo, ')
          ..write('version: $version, ')
          ..write('groupCode: $groupCode, ')
          ..write('utcOffset: $utcOffset')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    scope,
    fetchedAt,
    dateFrom,
    dateTo,
    version,
    groupCode,
    utcOffset,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is ScheduleMetaData &&
          other.scope == this.scope &&
          other.fetchedAt == this.fetchedAt &&
          other.dateFrom == this.dateFrom &&
          other.dateTo == this.dateTo &&
          other.version == this.version &&
          other.groupCode == this.groupCode &&
          other.utcOffset == this.utcOffset);
}

class ScheduleMetaCompanion extends UpdateCompanion<ScheduleMetaData> {
  final Value<String> scope;
  final Value<DateTime> fetchedAt;
  final Value<DateTime> dateFrom;
  final Value<DateTime> dateTo;
  final Value<String> version;
  final Value<String?> groupCode;
  final Value<int> utcOffset;
  final Value<int> rowid;
  const ScheduleMetaCompanion({
    this.scope = const Value.absent(),
    this.fetchedAt = const Value.absent(),
    this.dateFrom = const Value.absent(),
    this.dateTo = const Value.absent(),
    this.version = const Value.absent(),
    this.groupCode = const Value.absent(),
    this.utcOffset = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  ScheduleMetaCompanion.insert({
    required String scope,
    required DateTime fetchedAt,
    required DateTime dateFrom,
    required DateTime dateTo,
    required String version,
    this.groupCode = const Value.absent(),
    this.utcOffset = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : scope = Value(scope),
       fetchedAt = Value(fetchedAt),
       dateFrom = Value(dateFrom),
       dateTo = Value(dateTo),
       version = Value(version);
  static Insertable<ScheduleMetaData> custom({
    Expression<String>? scope,
    Expression<DateTime>? fetchedAt,
    Expression<DateTime>? dateFrom,
    Expression<DateTime>? dateTo,
    Expression<String>? version,
    Expression<String>? groupCode,
    Expression<int>? utcOffset,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (scope != null) 'scope': scope,
      if (fetchedAt != null) 'fetched_at': fetchedAt,
      if (dateFrom != null) 'date_from': dateFrom,
      if (dateTo != null) 'date_to': dateTo,
      if (version != null) 'version': version,
      if (groupCode != null) 'group_code': groupCode,
      if (utcOffset != null) 'utc_offset': utcOffset,
      if (rowid != null) 'rowid': rowid,
    });
  }

  ScheduleMetaCompanion copyWith({
    Value<String>? scope,
    Value<DateTime>? fetchedAt,
    Value<DateTime>? dateFrom,
    Value<DateTime>? dateTo,
    Value<String>? version,
    Value<String?>? groupCode,
    Value<int>? utcOffset,
    Value<int>? rowid,
  }) {
    return ScheduleMetaCompanion(
      scope: scope ?? this.scope,
      fetchedAt: fetchedAt ?? this.fetchedAt,
      dateFrom: dateFrom ?? this.dateFrom,
      dateTo: dateTo ?? this.dateTo,
      version: version ?? this.version,
      groupCode: groupCode ?? this.groupCode,
      utcOffset: utcOffset ?? this.utcOffset,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (scope.present) {
      map['scope'] = Variable<String>(scope.value);
    }
    if (fetchedAt.present) {
      map['fetched_at'] = Variable<DateTime>(fetchedAt.value);
    }
    if (dateFrom.present) {
      map['date_from'] = Variable<DateTime>(dateFrom.value);
    }
    if (dateTo.present) {
      map['date_to'] = Variable<DateTime>(dateTo.value);
    }
    if (version.present) {
      map['version'] = Variable<String>(version.value);
    }
    if (groupCode.present) {
      map['group_code'] = Variable<String>(groupCode.value);
    }
    if (utcOffset.present) {
      map['utc_offset'] = Variable<int>(utcOffset.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ScheduleMetaCompanion(')
          ..write('scope: $scope, ')
          ..write('fetchedAt: $fetchedAt, ')
          ..write('dateFrom: $dateFrom, ')
          ..write('dateTo: $dateTo, ')
          ..write('version: $version, ')
          ..write('groupCode: $groupCode, ')
          ..write('utcOffset: $utcOffset, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CachedChatsTable extends CachedChats
    with TableInfo<$CachedChatsTable, CachedChat> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedChatsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _titleMeta = const VerificationMeta('title');
  @override
  late final GeneratedColumn<String> title = GeneratedColumn<String>(
    'title',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _updatedAtMeta = const VerificationMeta(
    'updatedAt',
  );
  @override
  late final GeneratedColumn<DateTime> updatedAt = GeneratedColumn<DateTime>(
    'updated_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _documentIdsMeta = const VerificationMeta(
    'documentIds',
  );
  @override
  late final GeneratedColumn<String> documentIds = GeneratedColumn<String>(
    'document_ids',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant(''),
  );
  @override
  List<GeneratedColumn> get $columns => [id, title, updatedAt, documentIds];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_chats';
  @override
  VerificationContext validateIntegrity(
    Insertable<CachedChat> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('title')) {
      context.handle(
        _titleMeta,
        title.isAcceptableOrUnknown(data['title']!, _titleMeta),
      );
    }
    if (data.containsKey('updated_at')) {
      context.handle(
        _updatedAtMeta,
        updatedAt.isAcceptableOrUnknown(data['updated_at']!, _updatedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_updatedAtMeta);
    }
    if (data.containsKey('document_ids')) {
      context.handle(
        _documentIdsMeta,
        documentIds.isAcceptableOrUnknown(
          data['document_ids']!,
          _documentIdsMeta,
        ),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CachedChat map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedChat(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      title: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}title'],
      ),
      updatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}updated_at'],
      )!,
      documentIds: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}document_ids'],
      )!,
    );
  }

  @override
  $CachedChatsTable createAlias(String alias) {
    return $CachedChatsTable(attachedDatabase, alias);
  }
}

class CachedChat extends DataClass implements Insertable<CachedChat> {
  final String id;
  final String? title;
  final DateTime updatedAt;
  final String documentIds;
  const CachedChat({
    required this.id,
    this.title,
    required this.updatedAt,
    required this.documentIds,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    if (!nullToAbsent || title != null) {
      map['title'] = Variable<String>(title);
    }
    map['updated_at'] = Variable<DateTime>(updatedAt);
    map['document_ids'] = Variable<String>(documentIds);
    return map;
  }

  CachedChatsCompanion toCompanion(bool nullToAbsent) {
    return CachedChatsCompanion(
      id: Value(id),
      title: title == null && nullToAbsent
          ? const Value.absent()
          : Value(title),
      updatedAt: Value(updatedAt),
      documentIds: Value(documentIds),
    );
  }

  factory CachedChat.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedChat(
      id: serializer.fromJson<String>(json['id']),
      title: serializer.fromJson<String?>(json['title']),
      updatedAt: serializer.fromJson<DateTime>(json['updatedAt']),
      documentIds: serializer.fromJson<String>(json['documentIds']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'title': serializer.toJson<String?>(title),
      'updatedAt': serializer.toJson<DateTime>(updatedAt),
      'documentIds': serializer.toJson<String>(documentIds),
    };
  }

  CachedChat copyWith({
    String? id,
    Value<String?> title = const Value.absent(),
    DateTime? updatedAt,
    String? documentIds,
  }) => CachedChat(
    id: id ?? this.id,
    title: title.present ? title.value : this.title,
    updatedAt: updatedAt ?? this.updatedAt,
    documentIds: documentIds ?? this.documentIds,
  );
  CachedChat copyWithCompanion(CachedChatsCompanion data) {
    return CachedChat(
      id: data.id.present ? data.id.value : this.id,
      title: data.title.present ? data.title.value : this.title,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
      documentIds: data.documentIds.present
          ? data.documentIds.value
          : this.documentIds,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedChat(')
          ..write('id: $id, ')
          ..write('title: $title, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('documentIds: $documentIds')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, title, updatedAt, documentIds);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedChat &&
          other.id == this.id &&
          other.title == this.title &&
          other.updatedAt == this.updatedAt &&
          other.documentIds == this.documentIds);
}

class CachedChatsCompanion extends UpdateCompanion<CachedChat> {
  final Value<String> id;
  final Value<String?> title;
  final Value<DateTime> updatedAt;
  final Value<String> documentIds;
  final Value<int> rowid;
  const CachedChatsCompanion({
    this.id = const Value.absent(),
    this.title = const Value.absent(),
    this.updatedAt = const Value.absent(),
    this.documentIds = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedChatsCompanion.insert({
    required String id,
    this.title = const Value.absent(),
    required DateTime updatedAt,
    this.documentIds = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       updatedAt = Value(updatedAt);
  static Insertable<CachedChat> custom({
    Expression<String>? id,
    Expression<String>? title,
    Expression<DateTime>? updatedAt,
    Expression<String>? documentIds,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (title != null) 'title': title,
      if (updatedAt != null) 'updated_at': updatedAt,
      if (documentIds != null) 'document_ids': documentIds,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedChatsCompanion copyWith({
    Value<String>? id,
    Value<String?>? title,
    Value<DateTime>? updatedAt,
    Value<String>? documentIds,
    Value<int>? rowid,
  }) {
    return CachedChatsCompanion(
      id: id ?? this.id,
      title: title ?? this.title,
      updatedAt: updatedAt ?? this.updatedAt,
      documentIds: documentIds ?? this.documentIds,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (title.present) {
      map['title'] = Variable<String>(title.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<DateTime>(updatedAt.value);
    }
    if (documentIds.present) {
      map['document_ids'] = Variable<String>(documentIds.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedChatsCompanion(')
          ..write('id: $id, ')
          ..write('title: $title, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('documentIds: $documentIds, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CachedMessagesTable extends CachedMessages
    with TableInfo<$CachedMessagesTable, CachedMessage> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedMessagesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _chatIdMeta = const VerificationMeta('chatId');
  @override
  late final GeneratedColumn<String> chatId = GeneratedColumn<String>(
    'chat_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _roleMeta = const VerificationMeta('role');
  @override
  late final GeneratedColumn<String> role = GeneratedColumn<String>(
    'role',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _contentMeta = const VerificationMeta(
    'content',
  );
  @override
  late final GeneratedColumn<String> content = GeneratedColumn<String>(
    'content',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _modeMeta = const VerificationMeta('mode');
  @override
  late final GeneratedColumn<String> mode = GeneratedColumn<String>(
    'mode',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _sourcesJsonMeta = const VerificationMeta(
    'sourcesJson',
  );
  @override
  late final GeneratedColumn<String> sourcesJson = GeneratedColumn<String>(
    'sources_json',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('[]'),
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    chatId,
    role,
    content,
    mode,
    sourcesJson,
    createdAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_messages';
  @override
  VerificationContext validateIntegrity(
    Insertable<CachedMessage> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('chat_id')) {
      context.handle(
        _chatIdMeta,
        chatId.isAcceptableOrUnknown(data['chat_id']!, _chatIdMeta),
      );
    } else if (isInserting) {
      context.missing(_chatIdMeta);
    }
    if (data.containsKey('role')) {
      context.handle(
        _roleMeta,
        role.isAcceptableOrUnknown(data['role']!, _roleMeta),
      );
    } else if (isInserting) {
      context.missing(_roleMeta);
    }
    if (data.containsKey('content')) {
      context.handle(
        _contentMeta,
        content.isAcceptableOrUnknown(data['content']!, _contentMeta),
      );
    } else if (isInserting) {
      context.missing(_contentMeta);
    }
    if (data.containsKey('mode')) {
      context.handle(
        _modeMeta,
        mode.isAcceptableOrUnknown(data['mode']!, _modeMeta),
      );
    } else if (isInserting) {
      context.missing(_modeMeta);
    }
    if (data.containsKey('sources_json')) {
      context.handle(
        _sourcesJsonMeta,
        sourcesJson.isAcceptableOrUnknown(
          data['sources_json']!,
          _sourcesJsonMeta,
        ),
      );
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CachedMessage map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedMessage(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      chatId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}chat_id'],
      )!,
      role: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}role'],
      )!,
      content: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}content'],
      )!,
      mode: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}mode'],
      )!,
      sourcesJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sources_json'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}created_at'],
      )!,
    );
  }

  @override
  $CachedMessagesTable createAlias(String alias) {
    return $CachedMessagesTable(attachedDatabase, alias);
  }
}

class CachedMessage extends DataClass implements Insertable<CachedMessage> {
  final String id;
  final String chatId;
  final String role;
  final String content;
  final String mode;
  final String sourcesJson;
  final DateTime createdAt;
  const CachedMessage({
    required this.id,
    required this.chatId,
    required this.role,
    required this.content,
    required this.mode,
    required this.sourcesJson,
    required this.createdAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['chat_id'] = Variable<String>(chatId);
    map['role'] = Variable<String>(role);
    map['content'] = Variable<String>(content);
    map['mode'] = Variable<String>(mode);
    map['sources_json'] = Variable<String>(sourcesJson);
    map['created_at'] = Variable<DateTime>(createdAt);
    return map;
  }

  CachedMessagesCompanion toCompanion(bool nullToAbsent) {
    return CachedMessagesCompanion(
      id: Value(id),
      chatId: Value(chatId),
      role: Value(role),
      content: Value(content),
      mode: Value(mode),
      sourcesJson: Value(sourcesJson),
      createdAt: Value(createdAt),
    );
  }

  factory CachedMessage.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedMessage(
      id: serializer.fromJson<String>(json['id']),
      chatId: serializer.fromJson<String>(json['chatId']),
      role: serializer.fromJson<String>(json['role']),
      content: serializer.fromJson<String>(json['content']),
      mode: serializer.fromJson<String>(json['mode']),
      sourcesJson: serializer.fromJson<String>(json['sourcesJson']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'chatId': serializer.toJson<String>(chatId),
      'role': serializer.toJson<String>(role),
      'content': serializer.toJson<String>(content),
      'mode': serializer.toJson<String>(mode),
      'sourcesJson': serializer.toJson<String>(sourcesJson),
      'createdAt': serializer.toJson<DateTime>(createdAt),
    };
  }

  CachedMessage copyWith({
    String? id,
    String? chatId,
    String? role,
    String? content,
    String? mode,
    String? sourcesJson,
    DateTime? createdAt,
  }) => CachedMessage(
    id: id ?? this.id,
    chatId: chatId ?? this.chatId,
    role: role ?? this.role,
    content: content ?? this.content,
    mode: mode ?? this.mode,
    sourcesJson: sourcesJson ?? this.sourcesJson,
    createdAt: createdAt ?? this.createdAt,
  );
  CachedMessage copyWithCompanion(CachedMessagesCompanion data) {
    return CachedMessage(
      id: data.id.present ? data.id.value : this.id,
      chatId: data.chatId.present ? data.chatId.value : this.chatId,
      role: data.role.present ? data.role.value : this.role,
      content: data.content.present ? data.content.value : this.content,
      mode: data.mode.present ? data.mode.value : this.mode,
      sourcesJson: data.sourcesJson.present
          ? data.sourcesJson.value
          : this.sourcesJson,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedMessage(')
          ..write('id: $id, ')
          ..write('chatId: $chatId, ')
          ..write('role: $role, ')
          ..write('content: $content, ')
          ..write('mode: $mode, ')
          ..write('sourcesJson: $sourcesJson, ')
          ..write('createdAt: $createdAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, chatId, role, content, mode, sourcesJson, createdAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedMessage &&
          other.id == this.id &&
          other.chatId == this.chatId &&
          other.role == this.role &&
          other.content == this.content &&
          other.mode == this.mode &&
          other.sourcesJson == this.sourcesJson &&
          other.createdAt == this.createdAt);
}

class CachedMessagesCompanion extends UpdateCompanion<CachedMessage> {
  final Value<String> id;
  final Value<String> chatId;
  final Value<String> role;
  final Value<String> content;
  final Value<String> mode;
  final Value<String> sourcesJson;
  final Value<DateTime> createdAt;
  final Value<int> rowid;
  const CachedMessagesCompanion({
    this.id = const Value.absent(),
    this.chatId = const Value.absent(),
    this.role = const Value.absent(),
    this.content = const Value.absent(),
    this.mode = const Value.absent(),
    this.sourcesJson = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedMessagesCompanion.insert({
    required String id,
    required String chatId,
    required String role,
    required String content,
    required String mode,
    this.sourcesJson = const Value.absent(),
    required DateTime createdAt,
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       chatId = Value(chatId),
       role = Value(role),
       content = Value(content),
       mode = Value(mode),
       createdAt = Value(createdAt);
  static Insertable<CachedMessage> custom({
    Expression<String>? id,
    Expression<String>? chatId,
    Expression<String>? role,
    Expression<String>? content,
    Expression<String>? mode,
    Expression<String>? sourcesJson,
    Expression<DateTime>? createdAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (chatId != null) 'chat_id': chatId,
      if (role != null) 'role': role,
      if (content != null) 'content': content,
      if (mode != null) 'mode': mode,
      if (sourcesJson != null) 'sources_json': sourcesJson,
      if (createdAt != null) 'created_at': createdAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedMessagesCompanion copyWith({
    Value<String>? id,
    Value<String>? chatId,
    Value<String>? role,
    Value<String>? content,
    Value<String>? mode,
    Value<String>? sourcesJson,
    Value<DateTime>? createdAt,
    Value<int>? rowid,
  }) {
    return CachedMessagesCompanion(
      id: id ?? this.id,
      chatId: chatId ?? this.chatId,
      role: role ?? this.role,
      content: content ?? this.content,
      mode: mode ?? this.mode,
      sourcesJson: sourcesJson ?? this.sourcesJson,
      createdAt: createdAt ?? this.createdAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (chatId.present) {
      map['chat_id'] = Variable<String>(chatId.value);
    }
    if (role.present) {
      map['role'] = Variable<String>(role.value);
    }
    if (content.present) {
      map['content'] = Variable<String>(content.value);
    }
    if (mode.present) {
      map['mode'] = Variable<String>(mode.value);
    }
    if (sourcesJson.present) {
      map['sources_json'] = Variable<String>(sourcesJson.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedMessagesCompanion(')
          ..write('id: $id, ')
          ..write('chatId: $chatId, ')
          ..write('role: $role, ')
          ..write('content: $content, ')
          ..write('mode: $mode, ')
          ..write('sourcesJson: $sourcesJson, ')
          ..write('createdAt: $createdAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDb extends GeneratedDatabase {
  _$AppDb(QueryExecutor e) : super(e);
  $AppDbManager get managers => $AppDbManager(this);
  late final $CachedLessonsTable cachedLessons = $CachedLessonsTable(this);
  late final $ScheduleMetaTable scheduleMeta = $ScheduleMetaTable(this);
  late final $CachedChatsTable cachedChats = $CachedChatsTable(this);
  late final $CachedMessagesTable cachedMessages = $CachedMessagesTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    cachedLessons,
    scheduleMeta,
    cachedChats,
    cachedMessages,
  ];
}

typedef $$CachedLessonsTableCreateCompanionBuilder =
    CachedLessonsCompanion Function({
      required String id,
      required String scope,
      required DateTime startsAt,
      required DateTime endsAt,
      required String subject,
      required String kind,
      Value<String?> room,
      Value<String?> campusRoomId,
      Value<String?> teacher,
      Value<String?> subgroup,
      Value<String?> note,
      required String status,
      Value<int> rowid,
    });
typedef $$CachedLessonsTableUpdateCompanionBuilder =
    CachedLessonsCompanion Function({
      Value<String> id,
      Value<String> scope,
      Value<DateTime> startsAt,
      Value<DateTime> endsAt,
      Value<String> subject,
      Value<String> kind,
      Value<String?> room,
      Value<String?> campusRoomId,
      Value<String?> teacher,
      Value<String?> subgroup,
      Value<String?> note,
      Value<String> status,
      Value<int> rowid,
    });

class $$CachedLessonsTableFilterComposer
    extends Composer<_$AppDb, $CachedLessonsTable> {
  $$CachedLessonsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get scope => $composableBuilder(
    column: $table.scope,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get startsAt => $composableBuilder(
    column: $table.startsAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get endsAt => $composableBuilder(
    column: $table.endsAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get subject => $composableBuilder(
    column: $table.subject,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get kind => $composableBuilder(
    column: $table.kind,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get room => $composableBuilder(
    column: $table.room,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get campusRoomId => $composableBuilder(
    column: $table.campusRoomId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get teacher => $composableBuilder(
    column: $table.teacher,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get subgroup => $composableBuilder(
    column: $table.subgroup,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get note => $composableBuilder(
    column: $table.note,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CachedLessonsTableOrderingComposer
    extends Composer<_$AppDb, $CachedLessonsTable> {
  $$CachedLessonsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get scope => $composableBuilder(
    column: $table.scope,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get startsAt => $composableBuilder(
    column: $table.startsAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get endsAt => $composableBuilder(
    column: $table.endsAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get subject => $composableBuilder(
    column: $table.subject,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get kind => $composableBuilder(
    column: $table.kind,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get room => $composableBuilder(
    column: $table.room,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get campusRoomId => $composableBuilder(
    column: $table.campusRoomId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get teacher => $composableBuilder(
    column: $table.teacher,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get subgroup => $composableBuilder(
    column: $table.subgroup,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get note => $composableBuilder(
    column: $table.note,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CachedLessonsTableAnnotationComposer
    extends Composer<_$AppDb, $CachedLessonsTable> {
  $$CachedLessonsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get scope =>
      $composableBuilder(column: $table.scope, builder: (column) => column);

  GeneratedColumn<DateTime> get startsAt =>
      $composableBuilder(column: $table.startsAt, builder: (column) => column);

  GeneratedColumn<DateTime> get endsAt =>
      $composableBuilder(column: $table.endsAt, builder: (column) => column);

  GeneratedColumn<String> get subject =>
      $composableBuilder(column: $table.subject, builder: (column) => column);

  GeneratedColumn<String> get kind =>
      $composableBuilder(column: $table.kind, builder: (column) => column);

  GeneratedColumn<String> get room =>
      $composableBuilder(column: $table.room, builder: (column) => column);

  GeneratedColumn<String> get campusRoomId => $composableBuilder(
    column: $table.campusRoomId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get teacher =>
      $composableBuilder(column: $table.teacher, builder: (column) => column);

  GeneratedColumn<String> get subgroup =>
      $composableBuilder(column: $table.subgroup, builder: (column) => column);

  GeneratedColumn<String> get note =>
      $composableBuilder(column: $table.note, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);
}

class $$CachedLessonsTableTableManager
    extends
        RootTableManager<
          _$AppDb,
          $CachedLessonsTable,
          CachedLesson,
          $$CachedLessonsTableFilterComposer,
          $$CachedLessonsTableOrderingComposer,
          $$CachedLessonsTableAnnotationComposer,
          $$CachedLessonsTableCreateCompanionBuilder,
          $$CachedLessonsTableUpdateCompanionBuilder,
          (
            CachedLesson,
            BaseReferences<_$AppDb, $CachedLessonsTable, CachedLesson>,
          ),
          CachedLesson,
          PrefetchHooks Function()
        > {
  $$CachedLessonsTableTableManager(_$AppDb db, $CachedLessonsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedLessonsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedLessonsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedLessonsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<String> scope = const Value.absent(),
                Value<DateTime> startsAt = const Value.absent(),
                Value<DateTime> endsAt = const Value.absent(),
                Value<String> subject = const Value.absent(),
                Value<String> kind = const Value.absent(),
                Value<String?> room = const Value.absent(),
                Value<String?> campusRoomId = const Value.absent(),
                Value<String?> teacher = const Value.absent(),
                Value<String?> subgroup = const Value.absent(),
                Value<String?> note = const Value.absent(),
                Value<String> status = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => CachedLessonsCompanion(
                id: id,
                scope: scope,
                startsAt: startsAt,
                endsAt: endsAt,
                subject: subject,
                kind: kind,
                room: room,
                campusRoomId: campusRoomId,
                teacher: teacher,
                subgroup: subgroup,
                note: note,
                status: status,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                required String scope,
                required DateTime startsAt,
                required DateTime endsAt,
                required String subject,
                required String kind,
                Value<String?> room = const Value.absent(),
                Value<String?> campusRoomId = const Value.absent(),
                Value<String?> teacher = const Value.absent(),
                Value<String?> subgroup = const Value.absent(),
                Value<String?> note = const Value.absent(),
                required String status,
                Value<int> rowid = const Value.absent(),
              }) => CachedLessonsCompanion.insert(
                id: id,
                scope: scope,
                startsAt: startsAt,
                endsAt: endsAt,
                subject: subject,
                kind: kind,
                room: room,
                campusRoomId: campusRoomId,
                teacher: teacher,
                subgroup: subgroup,
                note: note,
                status: status,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$CachedLessonsTable, CachedLesson>(table),
                  BaseReferences<_$AppDb, $CachedLessonsTable, CachedLesson>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CachedLessonsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDb,
      $CachedLessonsTable,
      CachedLesson,
      $$CachedLessonsTableFilterComposer,
      $$CachedLessonsTableOrderingComposer,
      $$CachedLessonsTableAnnotationComposer,
      $$CachedLessonsTableCreateCompanionBuilder,
      $$CachedLessonsTableUpdateCompanionBuilder,
      (
        CachedLesson,
        BaseReferences<_$AppDb, $CachedLessonsTable, CachedLesson>,
      ),
      CachedLesson,
      PrefetchHooks Function()
    >;
typedef $$ScheduleMetaTableCreateCompanionBuilder =
    ScheduleMetaCompanion Function({
      required String scope,
      required DateTime fetchedAt,
      required DateTime dateFrom,
      required DateTime dateTo,
      required String version,
      Value<String?> groupCode,
      Value<int> utcOffset,
      Value<int> rowid,
    });
typedef $$ScheduleMetaTableUpdateCompanionBuilder =
    ScheduleMetaCompanion Function({
      Value<String> scope,
      Value<DateTime> fetchedAt,
      Value<DateTime> dateFrom,
      Value<DateTime> dateTo,
      Value<String> version,
      Value<String?> groupCode,
      Value<int> utcOffset,
      Value<int> rowid,
    });

class $$ScheduleMetaTableFilterComposer
    extends Composer<_$AppDb, $ScheduleMetaTable> {
  $$ScheduleMetaTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get scope => $composableBuilder(
    column: $table.scope,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get fetchedAt => $composableBuilder(
    column: $table.fetchedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get dateFrom => $composableBuilder(
    column: $table.dateFrom,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get dateTo => $composableBuilder(
    column: $table.dateTo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get version => $composableBuilder(
    column: $table.version,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get groupCode => $composableBuilder(
    column: $table.groupCode,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get utcOffset => $composableBuilder(
    column: $table.utcOffset,
    builder: (column) => ColumnFilters(column),
  );
}

class $$ScheduleMetaTableOrderingComposer
    extends Composer<_$AppDb, $ScheduleMetaTable> {
  $$ScheduleMetaTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get scope => $composableBuilder(
    column: $table.scope,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get fetchedAt => $composableBuilder(
    column: $table.fetchedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get dateFrom => $composableBuilder(
    column: $table.dateFrom,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get dateTo => $composableBuilder(
    column: $table.dateTo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get version => $composableBuilder(
    column: $table.version,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get groupCode => $composableBuilder(
    column: $table.groupCode,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get utcOffset => $composableBuilder(
    column: $table.utcOffset,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$ScheduleMetaTableAnnotationComposer
    extends Composer<_$AppDb, $ScheduleMetaTable> {
  $$ScheduleMetaTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get scope =>
      $composableBuilder(column: $table.scope, builder: (column) => column);

  GeneratedColumn<DateTime> get fetchedAt =>
      $composableBuilder(column: $table.fetchedAt, builder: (column) => column);

  GeneratedColumn<DateTime> get dateFrom =>
      $composableBuilder(column: $table.dateFrom, builder: (column) => column);

  GeneratedColumn<DateTime> get dateTo =>
      $composableBuilder(column: $table.dateTo, builder: (column) => column);

  GeneratedColumn<String> get version =>
      $composableBuilder(column: $table.version, builder: (column) => column);

  GeneratedColumn<String> get groupCode =>
      $composableBuilder(column: $table.groupCode, builder: (column) => column);

  GeneratedColumn<int> get utcOffset =>
      $composableBuilder(column: $table.utcOffset, builder: (column) => column);
}

class $$ScheduleMetaTableTableManager
    extends
        RootTableManager<
          _$AppDb,
          $ScheduleMetaTable,
          ScheduleMetaData,
          $$ScheduleMetaTableFilterComposer,
          $$ScheduleMetaTableOrderingComposer,
          $$ScheduleMetaTableAnnotationComposer,
          $$ScheduleMetaTableCreateCompanionBuilder,
          $$ScheduleMetaTableUpdateCompanionBuilder,
          (
            ScheduleMetaData,
            BaseReferences<_$AppDb, $ScheduleMetaTable, ScheduleMetaData>,
          ),
          ScheduleMetaData,
          PrefetchHooks Function()
        > {
  $$ScheduleMetaTableTableManager(_$AppDb db, $ScheduleMetaTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ScheduleMetaTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ScheduleMetaTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ScheduleMetaTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> scope = const Value.absent(),
                Value<DateTime> fetchedAt = const Value.absent(),
                Value<DateTime> dateFrom = const Value.absent(),
                Value<DateTime> dateTo = const Value.absent(),
                Value<String> version = const Value.absent(),
                Value<String?> groupCode = const Value.absent(),
                Value<int> utcOffset = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => ScheduleMetaCompanion(
                scope: scope,
                fetchedAt: fetchedAt,
                dateFrom: dateFrom,
                dateTo: dateTo,
                version: version,
                groupCode: groupCode,
                utcOffset: utcOffset,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String scope,
                required DateTime fetchedAt,
                required DateTime dateFrom,
                required DateTime dateTo,
                required String version,
                Value<String?> groupCode = const Value.absent(),
                Value<int> utcOffset = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => ScheduleMetaCompanion.insert(
                scope: scope,
                fetchedAt: fetchedAt,
                dateFrom: dateFrom,
                dateTo: dateTo,
                version: version,
                groupCode: groupCode,
                utcOffset: utcOffset,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$ScheduleMetaTable, ScheduleMetaData>(table),
                  BaseReferences<_$AppDb, $ScheduleMetaTable, ScheduleMetaData>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$ScheduleMetaTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDb,
      $ScheduleMetaTable,
      ScheduleMetaData,
      $$ScheduleMetaTableFilterComposer,
      $$ScheduleMetaTableOrderingComposer,
      $$ScheduleMetaTableAnnotationComposer,
      $$ScheduleMetaTableCreateCompanionBuilder,
      $$ScheduleMetaTableUpdateCompanionBuilder,
      (
        ScheduleMetaData,
        BaseReferences<_$AppDb, $ScheduleMetaTable, ScheduleMetaData>,
      ),
      ScheduleMetaData,
      PrefetchHooks Function()
    >;
typedef $$CachedChatsTableCreateCompanionBuilder =
    CachedChatsCompanion Function({
      required String id,
      Value<String?> title,
      required DateTime updatedAt,
      Value<String> documentIds,
      Value<int> rowid,
    });
typedef $$CachedChatsTableUpdateCompanionBuilder =
    CachedChatsCompanion Function({
      Value<String> id,
      Value<String?> title,
      Value<DateTime> updatedAt,
      Value<String> documentIds,
      Value<int> rowid,
    });

class $$CachedChatsTableFilterComposer
    extends Composer<_$AppDb, $CachedChatsTable> {
  $$CachedChatsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get title => $composableBuilder(
    column: $table.title,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get documentIds => $composableBuilder(
    column: $table.documentIds,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CachedChatsTableOrderingComposer
    extends Composer<_$AppDb, $CachedChatsTable> {
  $$CachedChatsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get title => $composableBuilder(
    column: $table.title,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get documentIds => $composableBuilder(
    column: $table.documentIds,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CachedChatsTableAnnotationComposer
    extends Composer<_$AppDb, $CachedChatsTable> {
  $$CachedChatsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get title =>
      $composableBuilder(column: $table.title, builder: (column) => column);

  GeneratedColumn<DateTime> get updatedAt =>
      $composableBuilder(column: $table.updatedAt, builder: (column) => column);

  GeneratedColumn<String> get documentIds => $composableBuilder(
    column: $table.documentIds,
    builder: (column) => column,
  );
}

class $$CachedChatsTableTableManager
    extends
        RootTableManager<
          _$AppDb,
          $CachedChatsTable,
          CachedChat,
          $$CachedChatsTableFilterComposer,
          $$CachedChatsTableOrderingComposer,
          $$CachedChatsTableAnnotationComposer,
          $$CachedChatsTableCreateCompanionBuilder,
          $$CachedChatsTableUpdateCompanionBuilder,
          (CachedChat, BaseReferences<_$AppDb, $CachedChatsTable, CachedChat>),
          CachedChat,
          PrefetchHooks Function()
        > {
  $$CachedChatsTableTableManager(_$AppDb db, $CachedChatsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedChatsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedChatsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedChatsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<String?> title = const Value.absent(),
                Value<DateTime> updatedAt = const Value.absent(),
                Value<String> documentIds = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => CachedChatsCompanion(
                id: id,
                title: title,
                updatedAt: updatedAt,
                documentIds: documentIds,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                Value<String?> title = const Value.absent(),
                required DateTime updatedAt,
                Value<String> documentIds = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => CachedChatsCompanion.insert(
                id: id,
                title: title,
                updatedAt: updatedAt,
                documentIds: documentIds,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$CachedChatsTable, CachedChat>(table),
                  BaseReferences<_$AppDb, $CachedChatsTable, CachedChat>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CachedChatsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDb,
      $CachedChatsTable,
      CachedChat,
      $$CachedChatsTableFilterComposer,
      $$CachedChatsTableOrderingComposer,
      $$CachedChatsTableAnnotationComposer,
      $$CachedChatsTableCreateCompanionBuilder,
      $$CachedChatsTableUpdateCompanionBuilder,
      (CachedChat, BaseReferences<_$AppDb, $CachedChatsTable, CachedChat>),
      CachedChat,
      PrefetchHooks Function()
    >;
typedef $$CachedMessagesTableCreateCompanionBuilder =
    CachedMessagesCompanion Function({
      required String id,
      required String chatId,
      required String role,
      required String content,
      required String mode,
      Value<String> sourcesJson,
      required DateTime createdAt,
      Value<int> rowid,
    });
typedef $$CachedMessagesTableUpdateCompanionBuilder =
    CachedMessagesCompanion Function({
      Value<String> id,
      Value<String> chatId,
      Value<String> role,
      Value<String> content,
      Value<String> mode,
      Value<String> sourcesJson,
      Value<DateTime> createdAt,
      Value<int> rowid,
    });

class $$CachedMessagesTableFilterComposer
    extends Composer<_$AppDb, $CachedMessagesTable> {
  $$CachedMessagesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get chatId => $composableBuilder(
    column: $table.chatId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get role => $composableBuilder(
    column: $table.role,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get content => $composableBuilder(
    column: $table.content,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get mode => $composableBuilder(
    column: $table.mode,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get sourcesJson => $composableBuilder(
    column: $table.sourcesJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CachedMessagesTableOrderingComposer
    extends Composer<_$AppDb, $CachedMessagesTable> {
  $$CachedMessagesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get chatId => $composableBuilder(
    column: $table.chatId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get role => $composableBuilder(
    column: $table.role,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get content => $composableBuilder(
    column: $table.content,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get mode => $composableBuilder(
    column: $table.mode,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get sourcesJson => $composableBuilder(
    column: $table.sourcesJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CachedMessagesTableAnnotationComposer
    extends Composer<_$AppDb, $CachedMessagesTable> {
  $$CachedMessagesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get chatId =>
      $composableBuilder(column: $table.chatId, builder: (column) => column);

  GeneratedColumn<String> get role =>
      $composableBuilder(column: $table.role, builder: (column) => column);

  GeneratedColumn<String> get content =>
      $composableBuilder(column: $table.content, builder: (column) => column);

  GeneratedColumn<String> get mode =>
      $composableBuilder(column: $table.mode, builder: (column) => column);

  GeneratedColumn<String> get sourcesJson => $composableBuilder(
    column: $table.sourcesJson,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);
}

class $$CachedMessagesTableTableManager
    extends
        RootTableManager<
          _$AppDb,
          $CachedMessagesTable,
          CachedMessage,
          $$CachedMessagesTableFilterComposer,
          $$CachedMessagesTableOrderingComposer,
          $$CachedMessagesTableAnnotationComposer,
          $$CachedMessagesTableCreateCompanionBuilder,
          $$CachedMessagesTableUpdateCompanionBuilder,
          (
            CachedMessage,
            BaseReferences<_$AppDb, $CachedMessagesTable, CachedMessage>,
          ),
          CachedMessage,
          PrefetchHooks Function()
        > {
  $$CachedMessagesTableTableManager(_$AppDb db, $CachedMessagesTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedMessagesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedMessagesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedMessagesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<String> chatId = const Value.absent(),
                Value<String> role = const Value.absent(),
                Value<String> content = const Value.absent(),
                Value<String> mode = const Value.absent(),
                Value<String> sourcesJson = const Value.absent(),
                Value<DateTime> createdAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => CachedMessagesCompanion(
                id: id,
                chatId: chatId,
                role: role,
                content: content,
                mode: mode,
                sourcesJson: sourcesJson,
                createdAt: createdAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                required String chatId,
                required String role,
                required String content,
                required String mode,
                Value<String> sourcesJson = const Value.absent(),
                required DateTime createdAt,
                Value<int> rowid = const Value.absent(),
              }) => CachedMessagesCompanion.insert(
                id: id,
                chatId: chatId,
                role: role,
                content: content,
                mode: mode,
                sourcesJson: sourcesJson,
                createdAt: createdAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$CachedMessagesTable, CachedMessage>(table),
                  BaseReferences<_$AppDb, $CachedMessagesTable, CachedMessage>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CachedMessagesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDb,
      $CachedMessagesTable,
      CachedMessage,
      $$CachedMessagesTableFilterComposer,
      $$CachedMessagesTableOrderingComposer,
      $$CachedMessagesTableAnnotationComposer,
      $$CachedMessagesTableCreateCompanionBuilder,
      $$CachedMessagesTableUpdateCompanionBuilder,
      (
        CachedMessage,
        BaseReferences<_$AppDb, $CachedMessagesTable, CachedMessage>,
      ),
      CachedMessage,
      PrefetchHooks Function()
    >;

class $AppDbManager {
  final _$AppDb _db;
  $AppDbManager(this._db);
  $$CachedLessonsTableTableManager get cachedLessons =>
      $$CachedLessonsTableTableManager(_db, _db.cachedLessons);
  $$ScheduleMetaTableTableManager get scheduleMeta =>
      $$ScheduleMetaTableTableManager(_db, _db.scheduleMeta);
  $$CachedChatsTableTableManager get cachedChats =>
      $$CachedChatsTableTableManager(_db, _db.cachedChats);
  $$CachedMessagesTableTableManager get cachedMessages =>
      $$CachedMessagesTableTableManager(_db, _db.cachedMessages);
}
