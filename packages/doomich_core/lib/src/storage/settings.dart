import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Настройки устройства. Часть из них (группа "только на устройстве", имя
/// преподавателя) сознательно не уходит на сервер, см. docs/07-privacy-and-registration.md.
@immutable
class AppSettings {
  const AppSettings({
    this.themeMode = ThemeMode.system,
    this.localeCode,
    this.readAloud = false,
    this.speechRate = 1.0,
    this.voice,
    this.holdToTalk = true,
    this.deviceGroupId,
    this.deviceGroupCode,
    this.deviceSubgroup,
    this.teacherName,
    this.teacherKey,
    this.serverUrl,
    this.acceptedTermsVersion = 0,
    this.onboardingDone = false,
    this.incognitoByDefault = false,
    this.notifyScheduleChanges = true,
    this.lastChangesCheck,
    this.extra = const {},
  });

  final ThemeMode themeMode;

  /// ru, en или null (как в системе)
  final String? localeCode;
  final bool readAloud;
  final double speechRate;
  final String? voice;

  /// true: удерживать кнопку микрофона; false: нажать для старта и ещё раз для отправки
  final bool holdToTalk;

  /// Группа, выбранная только на устройстве (на сервер не отправляется как часть профиля)
  final String? deviceGroupId;
  final String? deviceGroupCode;
  final String? deviceSubgroup;

  /// Преподаватель: своё имя хранится только здесь, на сервер уходит лишь ключ
  final String? teacherName;
  final String? teacherKey;
  final String? serverUrl;
  final int acceptedTermsVersion;
  final bool onboardingDone;
  final bool incognitoByDefault;
  final bool notifyScheduleChanges;
  final DateTime? lastChangesCheck;

  /// Прочие ключи для функций следующих релизов
  final Map<String, Object?> extra;

  Locale? get locale => localeCode == null ? null : Locale(localeCode!);

  AppSettings copyWith({
    ThemeMode? themeMode,
    Object? localeCode = _keep,
    bool? readAloud,
    double? speechRate,
    Object? voice = _keep,
    bool? holdToTalk,
    Object? deviceGroupId = _keep,
    Object? deviceGroupCode = _keep,
    Object? deviceSubgroup = _keep,
    Object? teacherName = _keep,
    Object? teacherKey = _keep,
    Object? serverUrl = _keep,
    int? acceptedTermsVersion,
    bool? onboardingDone,
    bool? incognitoByDefault,
    bool? notifyScheduleChanges,
    Object? lastChangesCheck = _keep,
    Map<String, Object?>? extra,
  }) =>
      AppSettings(
        themeMode: themeMode ?? this.themeMode,
        localeCode: identical(localeCode, _keep) ? this.localeCode : localeCode as String?,
        readAloud: readAloud ?? this.readAloud,
        speechRate: speechRate ?? this.speechRate,
        voice: identical(voice, _keep) ? this.voice : voice as String?,
        holdToTalk: holdToTalk ?? this.holdToTalk,
        deviceGroupId: identical(deviceGroupId, _keep) ? this.deviceGroupId : deviceGroupId as String?,
        deviceGroupCode: identical(deviceGroupCode, _keep) ? this.deviceGroupCode : deviceGroupCode as String?,
        deviceSubgroup: identical(deviceSubgroup, _keep) ? this.deviceSubgroup : deviceSubgroup as String?,
        teacherName: identical(teacherName, _keep) ? this.teacherName : teacherName as String?,
        teacherKey: identical(teacherKey, _keep) ? this.teacherKey : teacherKey as String?,
        serverUrl: identical(serverUrl, _keep) ? this.serverUrl : serverUrl as String?,
        acceptedTermsVersion: acceptedTermsVersion ?? this.acceptedTermsVersion,
        onboardingDone: onboardingDone ?? this.onboardingDone,
        incognitoByDefault: incognitoByDefault ?? this.incognitoByDefault,
        notifyScheduleChanges: notifyScheduleChanges ?? this.notifyScheduleChanges,
        lastChangesCheck: identical(lastChangesCheck, _keep) ? this.lastChangesCheck : lastChangesCheck as DateTime?,
        extra: extra ?? this.extra,
      );

  Map<String, Object?> toJson() => {
        'themeMode': themeMode.name,
        'localeCode': localeCode,
        'readAloud': readAloud,
        'speechRate': speechRate,
        'voice': voice,
        'holdToTalk': holdToTalk,
        'deviceGroupId': deviceGroupId,
        'deviceGroupCode': deviceGroupCode,
        'deviceSubgroup': deviceSubgroup,
        'teacherName': teacherName,
        'teacherKey': teacherKey,
        'serverUrl': serverUrl,
        'acceptedTermsVersion': acceptedTermsVersion,
        'onboardingDone': onboardingDone,
        'incognitoByDefault': incognitoByDefault,
        'notifyScheduleChanges': notifyScheduleChanges,
        'lastChangesCheck': lastChangesCheck?.toIso8601String(),
        'extra': extra,
      };

  factory AppSettings.fromJson(Map<String, dynamic> j) => AppSettings(
        themeMode: ThemeMode.values.firstWhere((m) => m.name == j['themeMode'], orElse: () => ThemeMode.system),
        localeCode: j['localeCode'] as String?,
        readAloud: j['readAloud'] as bool? ?? false,
        speechRate: (j['speechRate'] as num?)?.toDouble() ?? 1.0,
        voice: j['voice'] as String?,
        holdToTalk: j['holdToTalk'] as bool? ?? true,
        deviceGroupId: j['deviceGroupId'] as String?,
        deviceGroupCode: j['deviceGroupCode'] as String?,
        deviceSubgroup: j['deviceSubgroup'] as String?,
        teacherName: j['teacherName'] as String?,
        teacherKey: j['teacherKey'] as String?,
        serverUrl: j['serverUrl'] as String?,
        acceptedTermsVersion: (j['acceptedTermsVersion'] as num?)?.toInt() ?? 0,
        onboardingDone: j['onboardingDone'] as bool? ?? false,
        incognitoByDefault: j['incognitoByDefault'] as bool? ?? false,
        notifyScheduleChanges: j['notifyScheduleChanges'] as bool? ?? true,
        lastChangesCheck: j['lastChangesCheck'] == null ? null : DateTime.tryParse(j['lastChangesCheck'] as String),
        extra: Map<String, Object?>.from(j['extra'] as Map? ?? const {}),
      );
}

const _keep = Object();

class SettingsStore {
  SettingsStore(this._prefs);

  final SharedPreferences _prefs;
  static const _key = 'doomich.settings.v1';

  static Future<SettingsStore> open() async => SettingsStore(await SharedPreferences.getInstance());

  AppSettings load() {
    final raw = _prefs.getString(_key);
    if (raw == null) return const AppSettings();
    try {
      return AppSettings.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      return const AppSettings();
    }
  }

  Future<void> save(AppSettings s) => _prefs.setString(_key, jsonEncode(s.toJson()));

  Future<void> clear() => _prefs.remove(_key);
}
