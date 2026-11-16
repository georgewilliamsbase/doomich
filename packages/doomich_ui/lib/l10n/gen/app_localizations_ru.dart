// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Russian (`ru`).
class SRu extends S {
  SRu([String locale = 'ru']) : super(locale);

  @override
  String get appName => 'Думыч';

  @override
  String get tagline => 'ИИ-помощник студента и преподавателя';

  @override
  String get next => 'Далее';

  @override
  String get back => 'Назад';

  @override
  String get cancel => 'Отмена';

  @override
  String get save => 'Сохранить';

  @override
  String get done => 'Готово';

  @override
  String get retry => 'Повторить';

  @override
  String get delete => 'Удалить';

  @override
  String get rename => 'Переименовать';

  @override
  String get close => 'Закрыть';

  @override
  String get copy => 'Копировать';

  @override
  String get copied => 'Скопировано';

  @override
  String get search => 'Поиск';

  @override
  String get ok => 'Хорошо';

  @override
  String get loading => 'Загрузка...';

  @override
  String get send => 'Отправить';

  @override
  String get stop => 'Остановить';

  @override
  String get welcomeTitle => 'Привет! Я Думыч';

  @override
  String get welcomeBody =>
      'Отвечаю на вопросы текстом и голосом, знаю твоё расписание и разбираюсь в твоих методичках.';

  @override
  String get featureChat =>
      'Чат и голос: спроси \"Какая у меня следующая пара?\"';

  @override
  String get featureSchedule => 'Расписание группы, работает и без интернета';

  @override
  String get featureDocs =>
      'Ответы по PDF, DOCX и XLSX со ссылками на страницу';

  @override
  String get featurePrivacy => 'Без телефона и почты: только псевдоним';

  @override
  String get language => 'Язык';

  @override
  String get languageSystem => 'Как в системе';

  @override
  String get theme => 'Тема';

  @override
  String get themeSystem => 'Как в системе';

  @override
  String get themeLight => 'Светлая';

  @override
  String get themeDark => 'Тёмная';

  @override
  String get haveAccount => 'У меня уже есть аккаунт';

  @override
  String get start => 'Начать';

  @override
  String get inviteTitle => 'Код приглашения';

  @override
  String get inviteHint =>
      'Код вида ABCD-EFGH выдают в деканате или куратор группы.';

  @override
  String get inviteField => 'Код приглашения';

  @override
  String get inviteScan => 'Сканировать QR';

  @override
  String get inviteNoCode => 'Где взять код?';

  @override
  String get inviteNoCodeBody =>
      'Пока Думыч работает в пилоте, вход только по приглашениям. Спросите код у куратора группы или в деканате.';

  @override
  String inviteFor(String tenant) {
    return 'Код для: $tenant';
  }

  @override
  String get roleStudent => 'студент';

  @override
  String get roleTeacher => 'преподаватель';

  @override
  String get roleStaff => 'сотрудник';

  @override
  String get registerTitle => 'Создание аккаунта';

  @override
  String get nickname => 'Псевдоним';

  @override
  String get nicknameHint => '3-24 символа. Не используйте настоящее имя.';

  @override
  String get nicknameSuggest => 'Придумать';

  @override
  String get nicknameTaken => 'Этот псевдоним уже занят';

  @override
  String get nicknameInvalid =>
      'Буквы, цифры, точка, дефис и подчёркивание, от 3 до 24 символов';

  @override
  String get nicknameLooksLikeName =>
      'Похоже на имя и фамилию. Лучше выбрать псевдоним, по которому вас не узнать.';

  @override
  String get password => 'Пароль';

  @override
  String get passwordRepeat => 'Повторите пароль';

  @override
  String get passwordHint => 'Не меньше 10 символов';

  @override
  String get passwordMismatch => 'Пароли не совпадают';

  @override
  String get passwordWeak => 'Слабый';

  @override
  String get passwordFair => 'Средний';

  @override
  String get passwordGood => 'Хороший';

  @override
  String get passwordStrong => 'Сильный';

  @override
  String get createAccount => 'Создать аккаунт';

  @override
  String get recoveryTitle => 'Код восстановления';

  @override
  String get recoveryBody =>
      'Это единственный способ восстановить доступ, если забудете пароль: почты и телефона у нас нет. Сохраните код в надёжном месте.';

  @override
  String get recoverySaveFile => 'Сохранить в файл';

  @override
  String get recoveryShare => 'Поделиться';

  @override
  String get recoveryConfirm => 'Я сохранил код восстановления';

  @override
  String get termsTitle => 'Правила и данные';

  @override
  String get termsAccept => 'Принимаю правила';

  @override
  String get termsOpen => 'Пользовательское соглашение';

  @override
  String get dataOpen => 'Какие данные мы обрабатываем';

  @override
  String get groupTitle => 'Ваша группа';

  @override
  String get groupBody =>
      'Группа нужна для расписания. Её можно хранить на сервере (тогда ассистент знает её на всех устройствах) или только на этом устройстве.';

  @override
  String get groupSearch => 'Найти группу';

  @override
  String get groupOnServer => 'Хранить на сервере';

  @override
  String get groupOnDevice => 'Только на этом устройстве';

  @override
  String get groupLater => 'Выбрать позже';

  @override
  String get subgroup => 'Подгруппа';

  @override
  String get subgroupAny => 'Без подгруппы';

  @override
  String get loginTitle => 'Вход';

  @override
  String get login => 'Войти';

  @override
  String get forgotPassword => 'Забыли пароль?';

  @override
  String get recoverTitle => 'Восстановление доступа';

  @override
  String get recoveryCode => 'Код восстановления';

  @override
  String get newPassword => 'Новый пароль';

  @override
  String get recover => 'Восстановить';

  @override
  String get newRecoveryCode => 'Новый код восстановления';

  @override
  String get newRecoveryCodeBody =>
      'Старый код больше не работает. Сохраните новый.';

  @override
  String get qrLoginTitle => 'Вход по QR с телефона';

  @override
  String get qrLoginBody =>
      'Откройте Думыч на телефоне: Настройки, Войти на ПК, и наведите камеру на код.';

  @override
  String get qrApproveTitle => 'Войти на компьютере?';

  @override
  String get qrApproveBody =>
      'Подтвердите, только если код показан на вашем компьютере.';

  @override
  String get qrApprove => 'Войти';

  @override
  String get signInOnPc => 'Войти на ПК';

  @override
  String get tabChat => 'Чат';

  @override
  String get tabSchedule => 'Расписание';

  @override
  String get tabDocuments => 'Документы';

  @override
  String get tabSettings => 'Настройки';

  @override
  String get tabMore => 'Ещё';

  @override
  String get chats => 'Чаты';

  @override
  String get newChat => 'Новый чат';

  @override
  String get incognito => 'Инкогнито';

  @override
  String get incognitoHint =>
      'Этот чат не сохраняется на сервере и исчезнет после закрытия.';

  @override
  String get chatEmpty =>
      'Спросите что угодно: объясню тему, помогу с задачей, найду ответ в методичке.';

  @override
  String get chatSuggest1 => 'Какая у меня следующая пара?';

  @override
  String get chatSuggest2 => 'Объясни производную простыми словами';

  @override
  String get chatSuggest3 => 'Когда экзамен по физике?';

  @override
  String get messageHint => 'Сообщение';

  @override
  String get holdToTalk => 'Удерживайте, чтобы говорить';

  @override
  String get tapToTalk => 'Нажмите, чтобы говорить';

  @override
  String get listening => 'Слушаю...';

  @override
  String get thinking => 'Думаю...';

  @override
  String get speaking => 'Отвечаю';

  @override
  String get readAloud => 'Читать ответы вслух';

  @override
  String get speak => 'Озвучить';

  @override
  String get attachDocument => 'Спросить по документу';

  @override
  String get toolSchedule => 'Смотрю расписание';

  @override
  String get toolDocuments => 'Ищу в документах';

  @override
  String get toolGeneric => 'Работаю с данными вуза';

  @override
  String get sources => 'Источники';

  @override
  String page(String page) {
    return 'стр. $page';
  }

  @override
  String sheet(String sheet) {
    return 'лист $sheet';
  }

  @override
  String get feedbackGood => 'Хороший ответ';

  @override
  String get feedbackBad => 'Плохой ответ';

  @override
  String get feedbackTitle => 'Что не так?';

  @override
  String get feedbackWrong => 'Ответ неверный';

  @override
  String get feedbackNoSource => 'Нет ссылки на источник';

  @override
  String get feedbackVoice => 'Плохо распознал или озвучил';

  @override
  String get feedbackOther => 'Другое';

  @override
  String get feedbackComment => 'Комментарий (необязательно)';

  @override
  String get feedbackShare =>
      'Приложить вопрос и ответ, чтобы команда разобралась';

  @override
  String get feedbackThanks => 'Спасибо за оценку!';

  @override
  String get aiNotice => 'Ответы генерирует ИИ и могут содержать ошибки.';

  @override
  String get today => 'Сегодня';

  @override
  String get tomorrow => 'Завтра';

  @override
  String get week => 'Неделя';

  @override
  String get day => 'День';

  @override
  String get nowLesson => 'Сейчас';

  @override
  String get nextLesson => 'Далее';

  @override
  String get noLessons => 'Занятий нет';

  @override
  String get noGroup => 'Группа не выбрана';

  @override
  String get chooseGroup => 'Выбрать группу';

  @override
  String offlineUpdated(String time) {
    return 'Без сети. Обновлено $time';
  }

  @override
  String get cancelled => 'Отменено';

  @override
  String room(String room) {
    return 'ауд. $room';
  }

  @override
  String get teacherMode => 'Расписание преподавателя';

  @override
  String get teacherName => 'Ваше имя как в расписании';

  @override
  String get teacherNameHint =>
      'Хранится только на этом устройстве, на сервер уходит лишь обезличенный ключ.';

  @override
  String get kindLecture => 'Лекция';

  @override
  String get kindPractice => 'Практика';

  @override
  String get kindLab => 'Лабораторная';

  @override
  String get kindExam => 'Экзамен';

  @override
  String get kindCredit => 'Зачёт';

  @override
  String get kindConsultation => 'Консультация';

  @override
  String get kindOther => 'Занятие';

  @override
  String get documents => 'Документы';

  @override
  String get upload => 'Загрузить';

  @override
  String get documentsEmpty =>
      'Загрузите методичку, конспект или таблицу, и я буду отвечать по ним со ссылками на страницы.';

  @override
  String get docLimits => 'PDF, DOCX, XLSX, PPTX до 20 МБ';

  @override
  String get statusProcessing => 'Обрабатывается';

  @override
  String get statusReady => 'Готов';

  @override
  String get statusFailed => 'Ошибка';

  @override
  String get askDocument => 'Спросить по документу';

  @override
  String get deleteDocument => 'Удалить документ?';

  @override
  String get deleteDocumentBody => 'Файл и его индекс удалятся с сервера.';

  @override
  String pages(int count) {
    return '$count стр.';
  }

  @override
  String get sourceTitle => 'Фрагмент документа';

  @override
  String get settings => 'Настройки';

  @override
  String get appearance => 'Оформление';

  @override
  String get voice => 'Голос';

  @override
  String get speechRate => 'Скорость речи';

  @override
  String get pttMode => 'Режим кнопки микрофона';

  @override
  String get pttHold => 'Удерживать';

  @override
  String get pttToggle => 'Нажать и ещё раз нажать';

  @override
  String get privacy => 'Приватность';

  @override
  String get historyRetention => 'Хранить историю чатов';

  @override
  String days(int count) {
    return '$count дн.';
  }

  @override
  String get dontStore => 'Не хранить';

  @override
  String get incognitoDefault => 'Новые чаты в режиме инкогнито';

  @override
  String get account => 'Аккаунт';

  @override
  String get changePassword => 'Сменить пароль';

  @override
  String get oldPassword => 'Текущий пароль';

  @override
  String get sessions => 'Устройства';

  @override
  String get thisDevice => 'Это устройство';

  @override
  String get logout => 'Выйти';

  @override
  String get deleteAccount => 'Удалить аккаунт';

  @override
  String get deleteAccountBody =>
      'Чаты, документы и настройки удалятся сразу, из резервных копий в течение 30 дней. Отменить нельзя.';

  @override
  String get confirmPassword => 'Введите пароль для подтверждения';

  @override
  String get about => 'О приложении';

  @override
  String version(String version) {
    return 'Версия $version';
  }

  @override
  String get reportProblem => 'Сообщить о проблеме';

  @override
  String get legal => 'Документы';

  @override
  String updateAvailable(String version) {
    return 'Доступна версия $version';
  }

  @override
  String get updateInstall => 'Обновить';

  @override
  String get errNetwork => 'Нет связи с сервером. Проверьте интернет.';

  @override
  String get errBadCredentials => 'Неверный псевдоним или пароль';

  @override
  String get errRateLimited => 'Слишком много попыток. Подождите немного.';

  @override
  String get errInviteInvalid => 'Код не найден. Проверьте, нет ли опечатки.';

  @override
  String get errInviteUsed => 'Этот код уже использован';

  @override
  String get errInviteExpired => 'Срок действия кода истёк';

  @override
  String get errInviteRevoked => 'Код отозван';

  @override
  String get errPasswordWeak => 'Пароль слишком простой';

  @override
  String get errBadRecovery => 'Неверный псевдоним или код восстановления';

  @override
  String get errFileTooLarge => 'Файл больше 20 МБ';

  @override
  String get errUnsupportedType => 'Поддерживаются PDF, DOCX, XLSX и PPTX';

  @override
  String get errDocumentsLimit => 'Достигнут лимит документов';

  @override
  String get errNoSpeech => 'Не расслышал. Попробуйте ещё раз.';

  @override
  String get errMicPermission =>
      'Нет доступа к микрофону. Разрешите его в настройках.';

  @override
  String get errLlm => 'Ассистент сейчас недоступен. Попробуйте позже.';

  @override
  String get errHistoryDisabled =>
      'История отключена в настройках, чат откроется в режиме инкогнито.';

  @override
  String get errGeneric => 'Что-то пошло не так';

  @override
  String get errBlocked => 'Аккаунт заблокирован';

  @override
  String get docFailed_virus_found => 'Файл не прошёл антивирусную проверку';

  @override
  String get docFailed_needs_ocr => 'Похоже на скан без текста';

  @override
  String get docFailed_too_many_pages => 'Больше 300 страниц';

  @override
  String get docFailed_empty_document => 'В документе нет текста';

  @override
  String get docFailed_pdf_encrypted => 'PDF защищён паролем';

  @override
  String get hotkeyHint =>
      'Удерживайте Ctrl+Пробел, чтобы говорить. Ctrl+M: микрофон, Ctrl+N: новый чат';
}
