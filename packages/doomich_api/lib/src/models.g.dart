// Сгенерировано tools/gen_dart_models.py из docs/api/openapi.json. Руками не править.
// ignore_for_file: unnecessary_null_comparison, prefer_const_constructors

String _date(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

class AuthOut {
  final Tokens tokens;
  final MeOut user;

  const AuthOut({required this.tokens, required this.user});

  factory AuthOut.fromJson(Map<String, dynamic> j) => AuthOut(
        tokens: Tokens.fromJson(j['tokens'] as Map<String, dynamic>),
        user: MeOut.fromJson(j['user'] as Map<String, dynamic>),
      );

  Map<String, dynamic> toJson() => {
        'tokens': tokens.toJson(),
        'user': user.toJson(),
      };
}

class CampusOut {
  final String id;
  final String name;
  final String? address;
  final double? lat;
  final double? lon;

  const CampusOut({required this.id, required this.name, this.address, this.lat, this.lon});

  factory CampusOut.fromJson(Map<String, dynamic> j) => CampusOut(
        id: j['id'] as String,
        name: j['name'] as String,
        address: j['address'] == null ? null : j['address'] as String,
        lat: j['lat'] == null ? null : (j['lat'] as num).toDouble(),
        lon: j['lon'] == null ? null : (j['lon'] as num).toDouble(),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        if (address != null) 'address': address!,
        if (lat != null) 'lat': lat!,
        if (lon != null) 'lon': lon!,
      };
}

class ChangeOut {
  final int id;
  final String groupId;
  final String change;
  final Map<String, dynamic>? before;
  final Map<String, dynamic>? after;
  final DateTime lessonDate;
  final DateTime detectedAt;

  const ChangeOut({required this.id, required this.groupId, required this.change, this.before, this.after, required this.lessonDate, required this.detectedAt});

  factory ChangeOut.fromJson(Map<String, dynamic> j) => ChangeOut(
        id: (j['id'] as num).toInt(),
        groupId: j['group_id'] as String,
        change: j['change'] as String,
        before: j['before'] == null ? null : Map<String, dynamic>.from(j['before'] as Map),
        after: j['after'] == null ? null : Map<String, dynamic>.from(j['after'] as Map),
        lessonDate: DateTime.parse(j['lesson_date'] as String),
        detectedAt: DateTime.parse(j['detected_at'] as String),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'group_id': groupId,
        'change': change,
        if (before != null) 'before': before!,
        if (after != null) 'after': after!,
        'lesson_date': _date(lessonDate),
        'detected_at': detectedAt.toUtc().toIso8601String(),
      };
}

class ChatCreate {
  final String? title;
  final List<String>? documentIds;
  final String? lectureId;
  final String? courseId;

  const ChatCreate({this.title, this.documentIds, this.lectureId, this.courseId});

  factory ChatCreate.fromJson(Map<String, dynamic> j) => ChatCreate(
        title: j['title'] == null ? null : j['title'] as String,
        documentIds: j['document_ids'] == null ? null : (j['document_ids'] as List<dynamic>).map((e) => e as String).toList(),
        lectureId: j['lecture_id'] == null ? null : j['lecture_id'] as String,
        courseId: j['course_id'] == null ? null : j['course_id'] as String,
      );

  Map<String, dynamic> toJson() => {
        if (title != null) 'title': title!,
        if (documentIds != null) 'document_ids': documentIds!,
        if (lectureId != null) 'lecture_id': lectureId!,
        if (courseId != null) 'course_id': courseId!,
      };
}

class ChatOut {
  final String id;
  final String? title;
  final List<String> documentIds;
  final String? lectureId;
  final String? courseId;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime? expiresAt;

  const ChatOut({required this.id, this.title, required this.documentIds, this.lectureId, this.courseId, required this.createdAt, required this.updatedAt, this.expiresAt});

  factory ChatOut.fromJson(Map<String, dynamic> j) => ChatOut(
        id: j['id'] as String,
        title: j['title'] == null ? null : j['title'] as String,
        documentIds: (j['document_ids'] as List<dynamic>).map((e) => e as String).toList(),
        lectureId: j['lecture_id'] == null ? null : j['lecture_id'] as String,
        courseId: j['course_id'] == null ? null : j['course_id'] as String,
        createdAt: DateTime.parse(j['created_at'] as String),
        updatedAt: DateTime.parse(j['updated_at'] as String),
        expiresAt: j['expires_at'] == null ? null : DateTime.parse(j['expires_at'] as String),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        if (title != null) 'title': title!,
        'document_ids': documentIds,
        if (lectureId != null) 'lecture_id': lectureId!,
        if (courseId != null) 'course_id': courseId!,
        'created_at': createdAt.toUtc().toIso8601String(),
        'updated_at': updatedAt.toUtc().toIso8601String(),
        if (expiresAt != null) 'expires_at': expiresAt!.toUtc().toIso8601String(),
      };
}

class ChatPatch {
  final String title;

  const ChatPatch({required this.title});

  factory ChatPatch.fromJson(Map<String, dynamic> j) => ChatPatch(
        title: j['title'] as String,
      );

  Map<String, dynamic> toJson() => {
        'title': title,
      };
}

class ChunkOut {
  final String chunkId;
  final String documentId;
  final String title;
  final int? page;
  final String? sheet;
  final String? section;
  final String text;
  final String? prevText;
  final String? nextText;
  final Map<String, dynamic> meta;

  const ChunkOut({required this.chunkId, required this.documentId, required this.title, this.page, this.sheet, this.section, required this.text, this.prevText, this.nextText, this.meta = const {}});

  factory ChunkOut.fromJson(Map<String, dynamic> j) => ChunkOut(
        chunkId: j['chunk_id'] as String,
        documentId: j['document_id'] as String,
        title: j['title'] as String,
        page: j['page'] == null ? null : (j['page'] as num).toInt(),
        sheet: j['sheet'] == null ? null : j['sheet'] as String,
        section: j['section'] == null ? null : j['section'] as String,
        text: j['text'] as String,
        prevText: j['prev_text'] == null ? null : j['prev_text'] as String,
        nextText: j['next_text'] == null ? null : j['next_text'] as String,
        meta: j['meta'] == null ? {} : Map<String, dynamic>.from(j['meta'] as Map),
      );

  Map<String, dynamic> toJson() => {
        'chunk_id': chunkId,
        'document_id': documentId,
        'title': title,
        if (page != null) 'page': page!,
        if (sheet != null) 'sheet': sheet!,
        if (section != null) 'section': section!,
        'text': text,
        if (prevText != null) 'prev_text': prevText!,
        if (nextText != null) 'next_text': nextText!,
        'meta': meta,
      };
}

/// Данные с устройства для ответа. На сервере не сохраняются.
class ClientContextIn {
  final String? groupId;
  final String? subgroup;
  final String? teacherKey;
  final String? campusId;
  final String? locationNodeId;

  const ClientContextIn({this.groupId, this.subgroup, this.teacherKey, this.campusId, this.locationNodeId});

  factory ClientContextIn.fromJson(Map<String, dynamic> j) => ClientContextIn(
        groupId: j['group_id'] == null ? null : j['group_id'] as String,
        subgroup: j['subgroup'] == null ? null : j['subgroup'] as String,
        teacherKey: j['teacher_key'] == null ? null : j['teacher_key'] as String,
        campusId: j['campus_id'] == null ? null : j['campus_id'] as String,
        locationNodeId: j['location_node_id'] == null ? null : j['location_node_id'] as String,
      );

  Map<String, dynamic> toJson() => {
        if (groupId != null) 'group_id': groupId!,
        if (subgroup != null) 'subgroup': subgroup!,
        if (teacherKey != null) 'teacher_key': teacherKey!,
        if (campusId != null) 'campus_id': campusId!,
        if (locationNodeId != null) 'location_node_id': locationNodeId!,
      };
}

class DocumentOut {
  final String id;
  final String title;
  final String kind;
  final String scope;
  final int sizeBytes;
  final int? pages;
  final String status;
  final String? error;
  final DateTime createdAt;

  const DocumentOut({required this.id, required this.title, required this.kind, required this.scope, required this.sizeBytes, this.pages, required this.status, this.error, required this.createdAt});

  factory DocumentOut.fromJson(Map<String, dynamic> j) => DocumentOut(
        id: j['id'] as String,
        title: j['title'] as String,
        kind: j['kind'] as String,
        scope: j['scope'] as String,
        sizeBytes: (j['size_bytes'] as num).toInt(),
        pages: j['pages'] == null ? null : (j['pages'] as num).toInt(),
        status: j['status'] as String,
        error: j['error'] == null ? null : j['error'] as String,
        createdAt: DateTime.parse(j['created_at'] as String),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'kind': kind,
        'scope': scope,
        'size_bytes': sizeBytes,
        if (pages != null) 'pages': pages!,
        'status': status,
        if (error != null) 'error': error!,
        'created_at': createdAt.toUtc().toIso8601String(),
      };
}

class FeedbackIn {
  final int rating;
  final String? messageId;
  final String? comment;
  final String? category;
  final bool shareContent;
  final String? question;
  final String? answer;
  final String? modelVersion;
  final String? mode;

  const FeedbackIn({required this.rating, this.messageId, this.comment, this.category, this.shareContent = false, this.question, this.answer, this.modelVersion, this.mode});

  factory FeedbackIn.fromJson(Map<String, dynamic> j) => FeedbackIn(
        rating: (j['rating'] as num).toInt(),
        messageId: j['message_id'] == null ? null : j['message_id'] as String,
        comment: j['comment'] == null ? null : j['comment'] as String,
        category: j['category'] == null ? null : j['category'] as String,
        shareContent: j['share_content'] == null ? false : j['share_content'] as bool,
        question: j['question'] == null ? null : j['question'] as String,
        answer: j['answer'] == null ? null : j['answer'] as String,
        modelVersion: j['model_version'] == null ? null : j['model_version'] as String,
        mode: j['mode'] == null ? null : j['mode'] as String,
      );

  Map<String, dynamic> toJson() => {
        'rating': rating,
        if (messageId != null) 'message_id': messageId!,
        if (comment != null) 'comment': comment!,
        if (category != null) 'category': category!,
        'share_content': shareContent,
        if (question != null) 'question': question!,
        if (answer != null) 'answer': answer!,
        if (modelVersion != null) 'model_version': modelVersion!,
        if (mode != null) 'mode': mode!,
      };
}

class GroupBrief {
  final String id;
  final String code;
  final String? name;

  const GroupBrief({required this.id, required this.code, this.name});

  factory GroupBrief.fromJson(Map<String, dynamic> j) => GroupBrief(
        id: j['id'] as String,
        code: j['code'] as String,
        name: j['name'] == null ? null : j['name'] as String,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'code': code,
        if (name != null) 'name': name!,
      };
}

class GroupOut {
  final String id;
  final String code;
  final String? name;
  final String? faculty;
  final int? year;
  final List<String> subgroups;

  const GroupOut({required this.id, required this.code, this.name, this.faculty, this.year, this.subgroups = const []});

  factory GroupOut.fromJson(Map<String, dynamic> j) => GroupOut(
        id: j['id'] as String,
        code: j['code'] as String,
        name: j['name'] == null ? null : j['name'] as String,
        faculty: j['faculty'] == null ? null : j['faculty'] as String,
        year: j['year'] == null ? null : (j['year'] as num).toInt(),
        subgroups: j['subgroups'] == null ? [] : (j['subgroups'] as List<dynamic>).map((e) => e as String).toList(),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'code': code,
        if (name != null) 'name': name!,
        if (faculty != null) 'faculty': faculty!,
        if (year != null) 'year': year!,
        'subgroups': subgroups,
      };
}

class HistoryMessage {
  final String role;
  final String content;

  const HistoryMessage({required this.role, required this.content});

  factory HistoryMessage.fromJson(Map<String, dynamic> j) => HistoryMessage(
        role: j['role'] as String,
        content: j['content'] as String,
      );

  Map<String, dynamic> toJson() => {
        'role': role,
        'content': content,
      };
}

class IncognitoIn {
  final String text;
  final String mode;
  final List<String>? documentIds;
  final ClientContextIn? context;
  final List<HistoryMessage>? history;

  const IncognitoIn({required this.text, this.mode = 'text', this.documentIds, this.context, this.history});

  factory IncognitoIn.fromJson(Map<String, dynamic> j) => IncognitoIn(
        text: j['text'] as String,
        mode: j['mode'] == null ? 'text' : j['mode'] as String,
        documentIds: j['document_ids'] == null ? null : (j['document_ids'] as List<dynamic>).map((e) => e as String).toList(),
        context: j['context'] == null ? null : ClientContextIn.fromJson(j['context'] as Map<String, dynamic>),
        history: j['history'] == null ? null : (j['history'] as List<dynamic>).map((e) => HistoryMessage.fromJson(e as Map<String, dynamic>)).toList(),
      );

  Map<String, dynamic> toJson() => {
        'text': text,
        'mode': mode,
        if (documentIds != null) 'document_ids': documentIds!,
        if (context != null) 'context': context!.toJson(),
        if (history != null) 'history': history!.map((e) => e.toJson()).toList(),
      };
}

class InviteCheckIn {
  final String code;

  const InviteCheckIn({required this.code});

  factory InviteCheckIn.fromJson(Map<String, dynamic> j) => InviteCheckIn(
        code: j['code'] as String,
      );

  Map<String, dynamic> toJson() => {
        'code': code,
      };
}

class InviteCheckOut {
  final TenantBrief tenant;
  final String role;
  final GroupBrief? group;

  const InviteCheckOut({required this.tenant, required this.role, this.group});

  factory InviteCheckOut.fromJson(Map<String, dynamic> j) => InviteCheckOut(
        tenant: TenantBrief.fromJson(j['tenant'] as Map<String, dynamic>),
        role: j['role'] as String,
        group: j['group'] == null ? null : GroupBrief.fromJson(j['group'] as Map<String, dynamic>),
      );

  Map<String, dynamic> toJson() => {
        'tenant': tenant.toJson(),
        'role': role,
        if (group != null) 'group': group!.toJson(),
      };
}

class LessonOut {
  final String id;
  final String groupId;
  final String? subgroup;
  final String subject;
  final String kind;
  final DateTime startsAt;
  final DateTime endsAt;
  final String? room;
  final String? campusRoomId;
  final String? teacher;
  final String? teacherKey;
  final String? note;
  final String status;

  const LessonOut({required this.id, required this.groupId, this.subgroup, required this.subject, required this.kind, required this.startsAt, required this.endsAt, this.room, this.campusRoomId, this.teacher, this.teacherKey, this.note, required this.status});

  factory LessonOut.fromJson(Map<String, dynamic> j) => LessonOut(
        id: j['id'] as String,
        groupId: j['group_id'] as String,
        subgroup: j['subgroup'] == null ? null : j['subgroup'] as String,
        subject: j['subject'] as String,
        kind: j['kind'] as String,
        startsAt: DateTime.parse(j['starts_at'] as String),
        endsAt: DateTime.parse(j['ends_at'] as String),
        room: j['room'] == null ? null : j['room'] as String,
        campusRoomId: j['campus_room_id'] == null ? null : j['campus_room_id'] as String,
        teacher: j['teacher'] == null ? null : j['teacher'] as String,
        teacherKey: j['teacher_key'] == null ? null : j['teacher_key'] as String,
        note: j['note'] == null ? null : j['note'] as String,
        status: j['status'] as String,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'group_id': groupId,
        if (subgroup != null) 'subgroup': subgroup!,
        'subject': subject,
        'kind': kind,
        'starts_at': startsAt.toUtc().toIso8601String(),
        'ends_at': endsAt.toUtc().toIso8601String(),
        if (room != null) 'room': room!,
        if (campusRoomId != null) 'campus_room_id': campusRoomId!,
        if (teacher != null) 'teacher': teacher!,
        if (teacherKey != null) 'teacher_key': teacherKey!,
        if (note != null) 'note': note!,
        'status': status,
      };
}

class LoginCheckOut {
  final bool valid;
  final bool available;
  final List<String> problems;
  final List<String> warnings;

  const LoginCheckOut({required this.valid, required this.available, this.problems = const [], this.warnings = const []});

  factory LoginCheckOut.fromJson(Map<String, dynamic> j) => LoginCheckOut(
        valid: j['valid'] as bool,
        available: j['available'] as bool,
        problems: j['problems'] == null ? [] : (j['problems'] as List<dynamic>).map((e) => e as String).toList(),
        warnings: j['warnings'] == null ? [] : (j['warnings'] as List<dynamic>).map((e) => e as String).toList(),
      );

  Map<String, dynamic> toJson() => {
        'valid': valid,
        'available': available,
        'problems': problems,
        'warnings': warnings,
      };
}

class LoginIn {
  final String login;
  final String password;
  final String? platform;

  const LoginIn({required this.login, required this.password, this.platform});

  factory LoginIn.fromJson(Map<String, dynamic> j) => LoginIn(
        login: j['login'] as String,
        password: j['password'] as String,
        platform: j['platform'] == null ? null : j['platform'] as String,
      );

  Map<String, dynamic> toJson() => {
        'login': login,
        'password': password,
        if (platform != null) 'platform': platform!,
      };
}

class MeOut {
  final String id;
  final String login;
  final String role;
  final TenantBrief tenant;
  final GroupBrief? group;
  final String? subgroup;
  final String locale;
  final int historyDays;
  final bool isBeta;
  final DateTime createdOn;
  final Map<String, bool> features;

  const MeOut({required this.id, required this.login, required this.role, required this.tenant, this.group, this.subgroup, required this.locale, required this.historyDays, required this.isBeta, required this.createdOn, this.features = const {}});

  factory MeOut.fromJson(Map<String, dynamic> j) => MeOut(
        id: j['id'] as String,
        login: j['login'] as String,
        role: j['role'] as String,
        tenant: TenantBrief.fromJson(j['tenant'] as Map<String, dynamic>),
        group: j['group'] == null ? null : GroupBrief.fromJson(j['group'] as Map<String, dynamic>),
        subgroup: j['subgroup'] == null ? null : j['subgroup'] as String,
        locale: j['locale'] as String,
        historyDays: (j['history_days'] as num).toInt(),
        isBeta: j['is_beta'] as bool,
        createdOn: DateTime.parse(j['created_on'] as String),
        features: j['features'] == null ? {} : Map<String, bool>.from(j['features'] as Map),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'login': login,
        'role': role,
        'tenant': tenant.toJson(),
        if (group != null) 'group': group!.toJson(),
        if (subgroup != null) 'subgroup': subgroup!,
        'locale': locale,
        'history_days': historyDays,
        'is_beta': isBeta,
        'created_on': _date(createdOn),
        'features': features,
      };
}

class MePatch {
  final String? locale;
  final String? groupId;
  final bool clearGroup;
  final String? subgroup;
  final int? historyDays;

  const MePatch({this.locale, this.groupId, this.clearGroup = false, this.subgroup, this.historyDays});

  factory MePatch.fromJson(Map<String, dynamic> j) => MePatch(
        locale: j['locale'] == null ? null : j['locale'] as String,
        groupId: j['group_id'] == null ? null : j['group_id'] as String,
        clearGroup: j['clear_group'] == null ? false : j['clear_group'] as bool,
        subgroup: j['subgroup'] == null ? null : j['subgroup'] as String,
        historyDays: j['history_days'] == null ? null : (j['history_days'] as num).toInt(),
      );

  Map<String, dynamic> toJson() => {
        if (locale != null) 'locale': locale!,
        if (groupId != null) 'group_id': groupId!,
        'clear_group': clearGroup,
        if (subgroup != null) 'subgroup': subgroup!,
        if (historyDays != null) 'history_days': historyDays!,
      };
}

class MessageIn {
  final String text;
  final String mode;
  final List<String>? documentIds;
  final ClientContextIn? context;

  const MessageIn({required this.text, this.mode = 'text', this.documentIds, this.context});

  factory MessageIn.fromJson(Map<String, dynamic> j) => MessageIn(
        text: j['text'] as String,
        mode: j['mode'] == null ? 'text' : j['mode'] as String,
        documentIds: j['document_ids'] == null ? null : (j['document_ids'] as List<dynamic>).map((e) => e as String).toList(),
        context: j['context'] == null ? null : ClientContextIn.fromJson(j['context'] as Map<String, dynamic>),
      );

  Map<String, dynamic> toJson() => {
        'text': text,
        'mode': mode,
        if (documentIds != null) 'document_ids': documentIds!,
        if (context != null) 'context': context!.toJson(),
      };
}

class MessageOut {
  final String id;
  final String role;
  final String content;
  final String mode;
  final List<Source> sources;
  final String? modelVersion;
  final DateTime createdAt;

  const MessageOut({required this.id, required this.role, required this.content, required this.mode, this.sources = const [], this.modelVersion, required this.createdAt});

  factory MessageOut.fromJson(Map<String, dynamic> j) => MessageOut(
        id: j['id'] as String,
        role: j['role'] as String,
        content: j['content'] as String,
        mode: j['mode'] as String,
        sources: j['sources'] == null ? [] : (j['sources'] as List<dynamic>).map((e) => Source.fromJson(e as Map<String, dynamic>)).toList(),
        modelVersion: j['model_version'] == null ? null : j['model_version'] as String,
        createdAt: DateTime.parse(j['created_at'] as String),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'role': role,
        'content': content,
        'mode': mode,
        'sources': sources.map((e) => e.toJson()).toList(),
        if (modelVersion != null) 'model_version': modelVersion!,
        'created_at': createdAt.toUtc().toIso8601String(),
      };
}

class NowNextOut {
  final LessonOut? current;
  final LessonOut? next;

  const NowNextOut({this.current, this.next});

  factory NowNextOut.fromJson(Map<String, dynamic> j) => NowNextOut(
        current: j['current'] == null ? null : LessonOut.fromJson(j['current'] as Map<String, dynamic>),
        next: j['next'] == null ? null : LessonOut.fromJson(j['next'] as Map<String, dynamic>),
      );

  Map<String, dynamic> toJson() => {
        if (current != null) 'current': current!.toJson(),
        if (next != null) 'next': next!.toJson(),
      };
}

class PasswordChangeIn {
  final String oldPassword;
  final String newPassword;

  const PasswordChangeIn({required this.oldPassword, required this.newPassword});

  factory PasswordChangeIn.fromJson(Map<String, dynamic> j) => PasswordChangeIn(
        oldPassword: j['old_password'] as String,
        newPassword: j['new_password'] as String,
      );

  Map<String, dynamic> toJson() => {
        'old_password': oldPassword,
        'new_password': newPassword,
      };
}

class PasswordIn {
  final String password;

  const PasswordIn({required this.password});

  factory PasswordIn.fromJson(Map<String, dynamic> j) => PasswordIn(
        password: j['password'] as String,
      );

  Map<String, dynamic> toJson() => {
        'password': password,
      };
}

class QrApproveIn {
  final String token;

  const QrApproveIn({required this.token});

  factory QrApproveIn.fromJson(Map<String, dynamic> j) => QrApproveIn(
        token: j['token'] as String,
      );

  Map<String, dynamic> toJson() => {
        'token': token,
      };
}

class QrPollIn {
  final String token;

  const QrPollIn({required this.token});

  factory QrPollIn.fromJson(Map<String, dynamic> j) => QrPollIn(
        token: j['token'] as String,
      );

  Map<String, dynamic> toJson() => {
        'token': token,
      };
}

class QrStartOut {
  final String token;
  final int expiresIn;

  const QrStartOut({required this.token, required this.expiresIn});

  factory QrStartOut.fromJson(Map<String, dynamic> j) => QrStartOut(
        token: j['token'] as String,
        expiresIn: (j['expires_in'] as num).toInt(),
      );

  Map<String, dynamic> toJson() => {
        'token': token,
        'expires_in': expiresIn,
      };
}

class RecoverIn {
  final String login;
  final String recoveryCode;
  final String newPassword;
  final String? platform;

  const RecoverIn({required this.login, required this.recoveryCode, required this.newPassword, this.platform});

  factory RecoverIn.fromJson(Map<String, dynamic> j) => RecoverIn(
        login: j['login'] as String,
        recoveryCode: j['recovery_code'] as String,
        newPassword: j['new_password'] as String,
        platform: j['platform'] == null ? null : j['platform'] as String,
      );

  Map<String, dynamic> toJson() => {
        'login': login,
        'recovery_code': recoveryCode,
        'new_password': newPassword,
        if (platform != null) 'platform': platform!,
      };
}

class RecoverOut {
  final Tokens tokens;
  final MeOut user;
  final String recoveryCode;

  const RecoverOut({required this.tokens, required this.user, required this.recoveryCode});

  factory RecoverOut.fromJson(Map<String, dynamic> j) => RecoverOut(
        tokens: Tokens.fromJson(j['tokens'] as Map<String, dynamic>),
        user: MeOut.fromJson(j['user'] as Map<String, dynamic>),
        recoveryCode: j['recovery_code'] as String,
      );

  Map<String, dynamic> toJson() => {
        'tokens': tokens.toJson(),
        'user': user.toJson(),
        'recovery_code': recoveryCode,
      };
}

class RecoveryCodeOut {
  final String recoveryCode;

  const RecoveryCodeOut({required this.recoveryCode});

  factory RecoveryCodeOut.fromJson(Map<String, dynamic> j) => RecoveryCodeOut(
        recoveryCode: j['recovery_code'] as String,
      );

  Map<String, dynamic> toJson() => {
        'recovery_code': recoveryCode,
      };
}

class RefreshIn {
  final String refreshToken;

  const RefreshIn({required this.refreshToken});

  factory RefreshIn.fromJson(Map<String, dynamic> j) => RefreshIn(
        refreshToken: j['refresh_token'] as String,
      );

  Map<String, dynamic> toJson() => {
        'refresh_token': refreshToken,
      };
}

class RegisterIn {
  final String inviteCode;
  final String login;
  final String password;
  final String locale;
  final String? platform;

  const RegisterIn({required this.inviteCode, required this.login, required this.password, this.locale = 'ru', this.platform});

  factory RegisterIn.fromJson(Map<String, dynamic> j) => RegisterIn(
        inviteCode: j['invite_code'] as String,
        login: j['login'] as String,
        password: j['password'] as String,
        locale: j['locale'] == null ? 'ru' : j['locale'] as String,
        platform: j['platform'] == null ? null : j['platform'] as String,
      );

  Map<String, dynamic> toJson() => {
        'invite_code': inviteCode,
        'login': login,
        'password': password,
        'locale': locale,
        if (platform != null) 'platform': platform!,
      };
}

class RegisterOut {
  final Tokens tokens;
  final MeOut user;
  final String recoveryCode;

  const RegisterOut({required this.tokens, required this.user, required this.recoveryCode});

  factory RegisterOut.fromJson(Map<String, dynamic> j) => RegisterOut(
        tokens: Tokens.fromJson(j['tokens'] as Map<String, dynamic>),
        user: MeOut.fromJson(j['user'] as Map<String, dynamic>),
        recoveryCode: j['recovery_code'] as String,
      );

  Map<String, dynamic> toJson() => {
        'tokens': tokens.toJson(),
        'user': user.toJson(),
        'recovery_code': recoveryCode,
      };
}

class ReleaseOut {
  final String version;
  final int build;
  final String url;
  final String sha256;
  final String? signature;
  final bool force;
  final String? notes;

  const ReleaseOut({required this.version, required this.build, required this.url, required this.sha256, this.signature, required this.force, this.notes});

  factory ReleaseOut.fromJson(Map<String, dynamic> j) => ReleaseOut(
        version: j['version'] as String,
        build: (j['build'] as num).toInt(),
        url: j['url'] as String,
        sha256: j['sha256'] as String,
        signature: j['signature'] == null ? null : j['signature'] as String,
        force: j['force'] as bool,
        notes: j['notes'] == null ? null : j['notes'] as String,
      );

  Map<String, dynamic> toJson() => {
        'version': version,
        'build': build,
        'url': url,
        'sha256': sha256,
        if (signature != null) 'signature': signature!,
        'force': force,
        if (notes != null) 'notes': notes!,
      };
}

class RoleUpgradeIn {
  final String code;

  const RoleUpgradeIn({required this.code});

  factory RoleUpgradeIn.fromJson(Map<String, dynamic> j) => RoleUpgradeIn(
        code: j['code'] as String,
      );

  Map<String, dynamic> toJson() => {
        'code': code,
      };
}

class ScheduleOut {
  final GroupOut? group;
  final DateTime dateFrom;
  final DateTime dateTo;
  final List<LessonOut> lessons;
  final String version;
  final DateTime generatedAt;
  final int utcOffsetMinutes;

  const ScheduleOut({this.group, required this.dateFrom, required this.dateTo, required this.lessons, required this.version, required this.generatedAt, required this.utcOffsetMinutes});

  factory ScheduleOut.fromJson(Map<String, dynamic> j) => ScheduleOut(
        group: j['group'] == null ? null : GroupOut.fromJson(j['group'] as Map<String, dynamic>),
        dateFrom: DateTime.parse(j['date_from'] as String),
        dateTo: DateTime.parse(j['date_to'] as String),
        lessons: (j['lessons'] as List<dynamic>).map((e) => LessonOut.fromJson(e as Map<String, dynamic>)).toList(),
        version: j['version'] as String,
        generatedAt: DateTime.parse(j['generated_at'] as String),
        utcOffsetMinutes: (j['utc_offset_minutes'] as num).toInt(),
      );

  Map<String, dynamic> toJson() => {
        if (group != null) 'group': group!.toJson(),
        'date_from': _date(dateFrom),
        'date_to': _date(dateTo),
        'lessons': lessons.map((e) => e.toJson()).toList(),
        'version': version,
        'generated_at': generatedAt.toUtc().toIso8601String(),
        'utc_offset_minutes': utcOffsetMinutes,
      };
}

class SessionOut {
  final String id;
  final String? platform;
  final DateTime createdOn;
  final bool current;

  const SessionOut({required this.id, this.platform, required this.createdOn, required this.current});

  factory SessionOut.fromJson(Map<String, dynamic> j) => SessionOut(
        id: j['id'] as String,
        platform: j['platform'] == null ? null : j['platform'] as String,
        createdOn: DateTime.parse(j['created_on'] as String),
        current: j['current'] as bool,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        if (platform != null) 'platform': platform!,
        'created_on': _date(createdOn),
        'current': current,
      };
}

class Source {
  final int n;
  final String chunkId;
  final String documentId;
  final String title;
  final int? page;
  final String? sheet;
  final String snippet;
  final bool cited;
  final double? start;

  const Source({required this.n, required this.chunkId, required this.documentId, required this.title, this.page, this.sheet, required this.snippet, this.cited = true, this.start});

  factory Source.fromJson(Map<String, dynamic> j) => Source(
        n: (j['n'] as num).toInt(),
        chunkId: j['chunk_id'] as String,
        documentId: j['document_id'] as String,
        title: j['title'] as String,
        page: j['page'] == null ? null : (j['page'] as num).toInt(),
        sheet: j['sheet'] == null ? null : j['sheet'] as String,
        snippet: j['snippet'] as String,
        cited: j['cited'] == null ? true : j['cited'] as bool,
        start: j['start'] == null ? null : (j['start'] as num).toDouble(),
      );

  Map<String, dynamic> toJson() => {
        'n': n,
        'chunk_id': chunkId,
        'document_id': documentId,
        'title': title,
        if (page != null) 'page': page!,
        if (sheet != null) 'sheet': sheet!,
        'snippet': snippet,
        'cited': cited,
        if (start != null) 'start': start!,
      };
}

class TeacherOut {
  final String key;
  final String name;

  const TeacherOut({required this.key, required this.name});

  factory TeacherOut.fromJson(Map<String, dynamic> j) => TeacherOut(
        key: j['key'] as String,
        name: j['name'] as String,
      );

  Map<String, dynamic> toJson() => {
        'key': key,
        'name': name,
      };
}

class TenantBrief {
  final String id;
  final String slug;
  final String name;
  final String? shortName;
  final String timezone;

  const TenantBrief({required this.id, required this.slug, required this.name, this.shortName, required this.timezone});

  factory TenantBrief.fromJson(Map<String, dynamic> j) => TenantBrief(
        id: j['id'] as String,
        slug: j['slug'] as String,
        name: j['name'] as String,
        shortName: j['short_name'] == null ? null : j['short_name'] as String,
        timezone: j['timezone'] as String,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'slug': slug,
        'name': name,
        if (shortName != null) 'short_name': shortName!,
        'timezone': timezone,
      };
}

class TenantOut {
  final String id;
  final String slug;
  final String name;
  final String? shortName;
  final String timezone;
  final String teacherNames;
  final Map<String, bool> features;
  final List<List<String>> bellSchedule;
  final List<CampusOut> campuses;
  final List<TermOut> terms;
  final String? supportContact;
  final int utcOffsetMinutes;

  const TenantOut({required this.id, required this.slug, required this.name, this.shortName, required this.timezone, required this.teacherNames, required this.features, required this.bellSchedule, required this.campuses, required this.terms, this.supportContact, this.utcOffsetMinutes = 180});

  factory TenantOut.fromJson(Map<String, dynamic> j) => TenantOut(
        id: j['id'] as String,
        slug: j['slug'] as String,
        name: j['name'] as String,
        shortName: j['short_name'] == null ? null : j['short_name'] as String,
        timezone: j['timezone'] as String,
        teacherNames: j['teacher_names'] as String,
        features: Map<String, bool>.from(j['features'] as Map),
        bellSchedule: (j['bell_schedule'] as List<dynamic>).map((e) => (e as List<dynamic>).map((e) => e as String).toList()).toList(),
        campuses: (j['campuses'] as List<dynamic>).map((e) => CampusOut.fromJson(e as Map<String, dynamic>)).toList(),
        terms: (j['terms'] as List<dynamic>).map((e) => TermOut.fromJson(e as Map<String, dynamic>)).toList(),
        supportContact: j['support_contact'] == null ? null : j['support_contact'] as String,
        utcOffsetMinutes: j['utc_offset_minutes'] == null ? 180 : (j['utc_offset_minutes'] as num).toInt(),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'slug': slug,
        'name': name,
        if (shortName != null) 'short_name': shortName!,
        'timezone': timezone,
        'teacher_names': teacherNames,
        'features': features,
        'bell_schedule': bellSchedule,
        'campuses': campuses.map((e) => e.toJson()).toList(),
        'terms': terms.map((e) => e.toJson()).toList(),
        if (supportContact != null) 'support_contact': supportContact!,
        'utc_offset_minutes': utcOffsetMinutes,
      };
}

class TermOut {
  final String name;
  final DateTime startsOn;
  final DateTime endsOn;
  final bool firstWeekOdd;

  const TermOut({required this.name, required this.startsOn, required this.endsOn, required this.firstWeekOdd});

  factory TermOut.fromJson(Map<String, dynamic> j) => TermOut(
        name: j['name'] as String,
        startsOn: DateTime.parse(j['starts_on'] as String),
        endsOn: DateTime.parse(j['ends_on'] as String),
        firstWeekOdd: j['first_week_odd'] as bool,
      );

  Map<String, dynamic> toJson() => {
        'name': name,
        'starts_on': _date(startsOn),
        'ends_on': _date(endsOn),
        'first_week_odd': firstWeekOdd,
      };
}

class Tokens {
  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final int expiresIn;
  final int refreshExpiresIn;

  const Tokens({required this.accessToken, required this.refreshToken, this.tokenType = 'bearer', required this.expiresIn, required this.refreshExpiresIn});

  factory Tokens.fromJson(Map<String, dynamic> j) => Tokens(
        accessToken: j['access_token'] as String,
        refreshToken: j['refresh_token'] as String,
        tokenType: j['token_type'] == null ? 'bearer' : j['token_type'] as String,
        expiresIn: (j['expires_in'] as num).toInt(),
        refreshExpiresIn: (j['refresh_expires_in'] as num).toInt(),
      );

  Map<String, dynamic> toJson() => {
        'access_token': accessToken,
        'refresh_token': refreshToken,
        'token_type': tokenType,
        'expires_in': expiresIn,
        'refresh_expires_in': refreshExpiresIn,
      };
}
