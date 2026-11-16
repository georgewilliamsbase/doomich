import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';
import 'package:path_provider/path_provider.dart';

part 'app_db.g.dart';

/// Кэш расписания для работы без сети.
class CachedLessons extends Table {
  TextColumn get id => text()();

  /// Ключ выборки: `g:<id группы>:<подгруппа>` или `t:<ключ преподавателя>`
  TextColumn get scope => text()();
  DateTimeColumn get startsAt => dateTime()();
  DateTimeColumn get endsAt => dateTime()();
  TextColumn get subject => text()();
  TextColumn get kind => text()();
  TextColumn get room => text().nullable()();
  TextColumn get campusRoomId => text().nullable()();
  TextColumn get teacher => text().nullable()();
  TextColumn get subgroup => text().nullable()();
  TextColumn get note => text().nullable()();
  TextColumn get status => text()();

  @override
  Set<Column> get primaryKey => {id, scope};
}

class ScheduleMeta extends Table {
  TextColumn get scope => text()();
  DateTimeColumn get fetchedAt => dateTime()();
  DateTimeColumn get dateFrom => dateTime()();
  DateTimeColumn get dateTo => dateTime()();
  TextColumn get version => text()();
  TextColumn get groupCode => text().nullable()();

  /// Смещение часового пояса вуза в минутах: расписание показывается по времени вуза
  IntColumn get utcOffset => integer().withDefault(const Constant(180))();

  @override
  Set<Column> get primaryKey => {scope};
}

/// Кэш списка чатов и сообщений, чтобы историю можно было читать без сети.
class CachedChats extends Table {
  TextColumn get id => text()();
  TextColumn get title => text().nullable()();
  DateTimeColumn get updatedAt => dateTime()();
  TextColumn get documentIds => text().withDefault(const Constant(''))();

  @override
  Set<Column> get primaryKey => {id};
}

class CachedMessages extends Table {
  TextColumn get id => text()();
  TextColumn get chatId => text()();
  TextColumn get role => text()();
  TextColumn get content => text()();
  TextColumn get mode => text()();
  TextColumn get sourcesJson => text().withDefault(const Constant('[]'))();
  DateTimeColumn get createdAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

@DriftDatabase(tables: [CachedLessons, ScheduleMeta, CachedChats, CachedMessages])
class AppDb extends _$AppDb {
  AppDb([QueryExecutor? executor]) : super(executor ?? _open());

  /// История версий схемы: 1 (R1.0), 2 (смещение часового пояса в ScheduleMeta).
  @override
  int get schemaVersion => 2;

  /// Здесь только кэш, его всегда можно скачать заново. Поэтому при смене схемы
  /// таблицы пересоздаются: проще и надёжнее пошаговых миграций.
  @override
  MigrationStrategy get migration => MigrationStrategy(
        onCreate: (m) => m.createAll(),
        onUpgrade: (m, from, to) async {
          for (final table in allTables.toList().reversed) {
            await m.deleteTable(table.actualTableName);
          }
          await m.createAll();
        },
      );

  static QueryExecutor _open() => driftDatabase(
        name: 'doomich',
        native: const DriftNativeOptions(databaseDirectory: getApplicationSupportDirectory),
      );

  /// Полная очистка при выходе из аккаунта и удалении данных.
  Future<void> wipe() => transaction(() async {
        for (final t in allTables) {
          await delete(t).go();
        }
      });
}
