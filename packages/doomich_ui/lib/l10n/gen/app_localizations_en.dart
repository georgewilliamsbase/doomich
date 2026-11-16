// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class SEn extends S {
  SEn([String locale = 'en']) : super(locale);

  @override
  String get appName => 'Doomich';

  @override
  String get tagline => 'AI assistant for students and teachers';

  @override
  String get next => 'Next';

  @override
  String get back => 'Back';

  @override
  String get cancel => 'Cancel';

  @override
  String get save => 'Save';

  @override
  String get done => 'Done';

  @override
  String get retry => 'Retry';

  @override
  String get delete => 'Delete';

  @override
  String get rename => 'Rename';

  @override
  String get close => 'Close';

  @override
  String get copy => 'Copy';

  @override
  String get copied => 'Copied';

  @override
  String get search => 'Search';

  @override
  String get ok => 'OK';

  @override
  String get loading => 'Loading...';

  @override
  String get send => 'Send';

  @override
  String get stop => 'Stop';

  @override
  String get welcomeTitle => 'Hi! I\'m Doomich';

  @override
  String get welcomeBody =>
      'I answer questions by text and voice, know your schedule and understand your study materials.';

  @override
  String get featureChat => 'Chat and voice: ask \"What is my next class?\"';

  @override
  String get featureSchedule => 'Group schedule, works offline too';

  @override
  String get featureDocs =>
      'Answers from PDF, DOCX and XLSX with page references';

  @override
  String get featurePrivacy => 'No phone or e-mail: just a nickname';

  @override
  String get language => 'Language';

  @override
  String get languageSystem => 'System';

  @override
  String get theme => 'Theme';

  @override
  String get themeSystem => 'System';

  @override
  String get themeLight => 'Light';

  @override
  String get themeDark => 'Dark';

  @override
  String get haveAccount => 'I already have an account';

  @override
  String get start => 'Get started';

  @override
  String get inviteTitle => 'Invitation code';

  @override
  String get inviteHint =>
      'A code like ABCD-EFGH is given by the dean\'s office or the group curator.';

  @override
  String get inviteField => 'Invitation code';

  @override
  String get inviteScan => 'Scan QR';

  @override
  String get inviteNoCode => 'Where do I get a code?';

  @override
  String get inviteNoCodeBody =>
      'During the pilot, sign-up is invitation only. Ask your group curator or the dean\'s office for a code.';

  @override
  String inviteFor(String tenant) {
    return 'Code for: $tenant';
  }

  @override
  String get roleStudent => 'student';

  @override
  String get roleTeacher => 'teacher';

  @override
  String get roleStaff => 'staff';

  @override
  String get registerTitle => 'Create account';

  @override
  String get nickname => 'Nickname';

  @override
  String get nicknameHint => '3-24 characters. Don\'t use your real name.';

  @override
  String get nicknameSuggest => 'Suggest';

  @override
  String get nicknameTaken => 'This nickname is taken';

  @override
  String get nicknameInvalid =>
      'Letters, digits, dot, dash and underscore, 3 to 24 characters';

  @override
  String get nicknameLooksLikeName =>
      'Looks like a real name. Better choose a nickname that doesn\'t identify you.';

  @override
  String get password => 'Password';

  @override
  String get passwordRepeat => 'Repeat password';

  @override
  String get passwordHint => 'At least 10 characters';

  @override
  String get passwordMismatch => 'Passwords do not match';

  @override
  String get passwordWeak => 'Weak';

  @override
  String get passwordFair => 'Fair';

  @override
  String get passwordGood => 'Good';

  @override
  String get passwordStrong => 'Strong';

  @override
  String get createAccount => 'Create account';

  @override
  String get recoveryTitle => 'Recovery code';

  @override
  String get recoveryBody =>
      'This is the only way to restore access if you forget your password: we don\'t have your e-mail or phone. Keep the code in a safe place.';

  @override
  String get recoverySaveFile => 'Save to file';

  @override
  String get recoveryShare => 'Share';

  @override
  String get recoveryConfirm => 'I have saved the recovery code';

  @override
  String get termsTitle => 'Terms and data';

  @override
  String get termsAccept => 'I accept the terms';

  @override
  String get termsOpen => 'User agreement';

  @override
  String get dataOpen => 'What data we process';

  @override
  String get groupTitle => 'Your group';

  @override
  String get groupBody =>
      'The group is used for the schedule. Store it on the server (the assistant knows it on all your devices) or only on this device.';

  @override
  String get groupSearch => 'Find group';

  @override
  String get groupOnServer => 'Store on server';

  @override
  String get groupOnDevice => 'Only on this device';

  @override
  String get groupLater => 'Choose later';

  @override
  String get subgroup => 'Subgroup';

  @override
  String get subgroupAny => 'No subgroup';

  @override
  String get loginTitle => 'Sign in';

  @override
  String get login => 'Sign in';

  @override
  String get forgotPassword => 'Forgot password?';

  @override
  String get recoverTitle => 'Restore access';

  @override
  String get recoveryCode => 'Recovery code';

  @override
  String get newPassword => 'New password';

  @override
  String get recover => 'Restore';

  @override
  String get newRecoveryCode => 'New recovery code';

  @override
  String get newRecoveryCodeBody =>
      'The old code no longer works. Save the new one.';

  @override
  String get qrLoginTitle => 'Sign in with phone QR';

  @override
  String get qrLoginBody =>
      'Open Doomich on your phone: Settings, Sign in on PC, and point the camera at the code.';

  @override
  String get qrApproveTitle => 'Sign in on the computer?';

  @override
  String get qrApproveBody =>
      'Confirm only if this code is shown on your own computer.';

  @override
  String get qrApprove => 'Sign in';

  @override
  String get signInOnPc => 'Sign in on PC';

  @override
  String get tabChat => 'Chat';

  @override
  String get tabSchedule => 'Schedule';

  @override
  String get tabDocuments => 'Documents';

  @override
  String get tabSettings => 'Settings';

  @override
  String get tabMore => 'More';

  @override
  String get chats => 'Chats';

  @override
  String get newChat => 'New chat';

  @override
  String get incognito => 'Incognito';

  @override
  String get incognitoHint =>
      'This chat is not saved on the server and disappears when closed.';

  @override
  String get chatEmpty =>
      'Ask anything: I\'ll explain a topic, help with a problem, find an answer in your notes.';

  @override
  String get chatSuggest1 => 'What is my next class?';

  @override
  String get chatSuggest2 => 'Explain derivatives in simple words';

  @override
  String get chatSuggest3 => 'When is the physics exam?';

  @override
  String get messageHint => 'Message';

  @override
  String get holdToTalk => 'Hold to talk';

  @override
  String get tapToTalk => 'Tap to talk';

  @override
  String get listening => 'Listening...';

  @override
  String get thinking => 'Thinking...';

  @override
  String get speaking => 'Speaking';

  @override
  String get readAloud => 'Read answers aloud';

  @override
  String get speak => 'Read aloud';

  @override
  String get attachDocument => 'Ask about a document';

  @override
  String get toolSchedule => 'Checking the schedule';

  @override
  String get toolDocuments => 'Searching documents';

  @override
  String get toolGeneric => 'Checking university data';

  @override
  String get sources => 'Sources';

  @override
  String page(String page) {
    return 'p. $page';
  }

  @override
  String sheet(String sheet) {
    return 'sheet $sheet';
  }

  @override
  String get feedbackGood => 'Good answer';

  @override
  String get feedbackBad => 'Bad answer';

  @override
  String get feedbackTitle => 'What went wrong?';

  @override
  String get feedbackWrong => 'The answer is wrong';

  @override
  String get feedbackNoSource => 'No source reference';

  @override
  String get feedbackVoice => 'Speech recognition or voice issue';

  @override
  String get feedbackOther => 'Other';

  @override
  String get feedbackComment => 'Comment (optional)';

  @override
  String get feedbackShare => 'Attach the question and answer for the team';

  @override
  String get feedbackThanks => 'Thanks for the feedback!';

  @override
  String get aiNotice => 'Answers are AI-generated and may contain mistakes.';

  @override
  String get today => 'Today';

  @override
  String get tomorrow => 'Tomorrow';

  @override
  String get week => 'Week';

  @override
  String get day => 'Day';

  @override
  String get nowLesson => 'Now';

  @override
  String get nextLesson => 'Next';

  @override
  String get noLessons => 'No classes';

  @override
  String get noGroup => 'No group selected';

  @override
  String get chooseGroup => 'Choose group';

  @override
  String offlineUpdated(String time) {
    return 'Offline. Updated $time';
  }

  @override
  String get cancelled => 'Cancelled';

  @override
  String room(String room) {
    return 'room $room';
  }

  @override
  String get teacherMode => 'Teacher schedule';

  @override
  String get teacherName => 'Your name as in the schedule';

  @override
  String get teacherNameHint =>
      'Stored only on this device, the server only gets an anonymous key.';

  @override
  String get kindLecture => 'Lecture';

  @override
  String get kindPractice => 'Practice';

  @override
  String get kindLab => 'Lab';

  @override
  String get kindExam => 'Exam';

  @override
  String get kindCredit => 'Credit';

  @override
  String get kindConsultation => 'Consultation';

  @override
  String get kindOther => 'Class';

  @override
  String get documents => 'Documents';

  @override
  String get upload => 'Upload';

  @override
  String get documentsEmpty =>
      'Upload a manual, notes or a spreadsheet, and I\'ll answer from them with page references.';

  @override
  String get docLimits => 'PDF, DOCX, XLSX, PPTX up to 20 MB';

  @override
  String get statusProcessing => 'Processing';

  @override
  String get statusReady => 'Ready';

  @override
  String get statusFailed => 'Failed';

  @override
  String get askDocument => 'Ask about this document';

  @override
  String get deleteDocument => 'Delete the document?';

  @override
  String get deleteDocumentBody =>
      'The file and its index will be removed from the server.';

  @override
  String pages(int count) {
    return '$count p.';
  }

  @override
  String get sourceTitle => 'Document fragment';

  @override
  String get settings => 'Settings';

  @override
  String get appearance => 'Appearance';

  @override
  String get voice => 'Voice';

  @override
  String get speechRate => 'Speech rate';

  @override
  String get pttMode => 'Microphone button mode';

  @override
  String get pttHold => 'Hold';

  @override
  String get pttToggle => 'Tap to start, tap to stop';

  @override
  String get privacy => 'Privacy';

  @override
  String get historyRetention => 'Keep chat history';

  @override
  String days(int count) {
    return '$count days';
  }

  @override
  String get dontStore => 'Don\'t keep';

  @override
  String get incognitoDefault => 'New chats in incognito mode';

  @override
  String get account => 'Account';

  @override
  String get changePassword => 'Change password';

  @override
  String get oldPassword => 'Current password';

  @override
  String get sessions => 'Devices';

  @override
  String get thisDevice => 'This device';

  @override
  String get logout => 'Sign out';

  @override
  String get deleteAccount => 'Delete account';

  @override
  String get deleteAccountBody =>
      'Chats, documents and settings are deleted immediately, and from backups within 30 days. This cannot be undone.';

  @override
  String get confirmPassword => 'Enter your password to confirm';

  @override
  String get about => 'About';

  @override
  String version(String version) {
    return 'Version $version';
  }

  @override
  String get reportProblem => 'Report a problem';

  @override
  String get legal => 'Legal';

  @override
  String updateAvailable(String version) {
    return 'Version $version is available';
  }

  @override
  String get updateInstall => 'Update';

  @override
  String get errNetwork => 'Cannot reach the server. Check your connection.';

  @override
  String get errBadCredentials => 'Wrong nickname or password';

  @override
  String get errRateLimited => 'Too many attempts. Please wait a bit.';

  @override
  String get errInviteInvalid => 'Code not found. Check for typos.';

  @override
  String get errInviteUsed => 'This code has already been used';

  @override
  String get errInviteExpired => 'The code has expired';

  @override
  String get errInviteRevoked => 'The code was revoked';

  @override
  String get errPasswordWeak => 'The password is too simple';

  @override
  String get errBadRecovery => 'Wrong nickname or recovery code';

  @override
  String get errFileTooLarge => 'The file is larger than 20 MB';

  @override
  String get errUnsupportedType => 'PDF, DOCX, XLSX and PPTX are supported';

  @override
  String get errDocumentsLimit => 'Document limit reached';

  @override
  String get errNoSpeech => 'I didn\'t catch that. Please try again.';

  @override
  String get errMicPermission =>
      'No microphone access. Allow it in the settings.';

  @override
  String get errLlm => 'The assistant is unavailable right now. Try later.';

  @override
  String get errHistoryDisabled =>
      'History is off in settings, the chat opens in incognito mode.';

  @override
  String get errGeneric => 'Something went wrong';

  @override
  String get errBlocked => 'Account is blocked';

  @override
  String get docFailed_virus_found => 'The file failed the antivirus check';

  @override
  String get docFailed_needs_ocr => 'Looks like a scan without text';

  @override
  String get docFailed_too_many_pages => 'More than 300 pages';

  @override
  String get docFailed_empty_document => 'The document has no text';

  @override
  String get docFailed_pdf_encrypted => 'The PDF is password-protected';

  @override
  String get hotkeyHint =>
      'Ctrl+Space: voice input, Ctrl+N: new chat, Ctrl+K: search';
}
