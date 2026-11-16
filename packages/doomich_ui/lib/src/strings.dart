import 'package:doomich_api/doomich_api.dart';
import 'package:flutter/widgets.dart';

import '../l10n/gen/app_localizations.dart';

export '../l10n/gen/app_localizations.dart';

extension L10nX on BuildContext {
  S get s => S.of(this);
}

/// Текст ошибки для пользователя по стабильному коду API.
String errorText(S s, Object error) {
  final code = error is ApiException ? error.code : (error is String ? error : 'internal');
  return switch (code) {
    'network' => s.errNetwork,
    'bad_credentials' => s.errBadCredentials,
    'rate_limited' => s.errRateLimited,
    'invite_invalid' || 'invite_wrong_kind' => s.errInviteInvalid,
    'invite_used_up' => s.errInviteUsed,
    'invite_expired' => s.errInviteExpired,
    'invite_revoked' => s.errInviteRevoked,
    'password_weak' => s.errPasswordWeak,
    'bad_recovery' => s.errBadRecovery,
    'login_taken' => s.nicknameTaken,
    'login_invalid' => s.nicknameInvalid,
    'file_too_large' || 'payload_too_large' => s.errFileTooLarge,
    'unsupported_type' => s.errUnsupportedType,
    'documents_limit' => s.errDocumentsLimit,
    'no_speech' => s.errNoSpeech,
    'mic_permission' => s.errMicPermission,
    'llm_unavailable' || 'llm_error' || 'service_unavailable' => s.errLlm,
    'history_disabled' => s.errHistoryDisabled,
    'account_blocked' => s.errBlocked,
    _ => s.errGeneric,
  };
}

String docFailure(S s, String? code) => switch (code) {
      'virus_found' => s.docFailed_virus_found,
      'needs_ocr' => s.docFailed_needs_ocr,
      'too_many_pages' => s.docFailed_too_many_pages,
      'empty_document' => s.docFailed_empty_document,
      'pdf_encrypted' => s.docFailed_pdf_encrypted,
      _ => s.statusFailed,
    };

String kindText(S s, String kind) => switch (kind) {
      'lecture' => s.kindLecture,
      'practice' => s.kindPractice,
      'lab' => s.kindLab,
      'exam' => s.kindExam,
      'credit' => s.kindCredit,
      'consultation' => s.kindConsultation,
      _ => s.kindOther,
    };

String roleText(S s, String role) => switch (role) {
      'teacher' => s.roleTeacher,
      'staff' => s.roleStaff,
      _ => s.roleStudent,
    };

String toolText(S s, String tool) => switch (tool) {
      'get_schedule' || 'next_lesson' || 'find_lessons' => s.toolSchedule,
      'search_documents' => s.toolDocuments,
      _ => s.toolGeneric,
    };

String hhmm(DateTime t) {
  final l = t.toLocal();
  return '${l.hour.toString().padLeft(2, '0')}:${l.minute.toString().padLeft(2, '0')}';
}
