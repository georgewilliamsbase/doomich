import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_ru.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of S
/// returned by `S.of(context)`.
///
/// Applications need to include `S.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'gen/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: S.localizationsDelegates,
///   supportedLocales: S.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the S.supportedLocales
/// property.
abstract class S {
  S(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static S of(BuildContext context) {
    return Localizations.of<S>(context, S)!;
  }

  static const LocalizationsDelegate<S> delegate = _SDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('ru'),
  ];

  /// No description provided for @appName.
  ///
  /// In ru, this message translates to:
  /// **'Думыч'**
  String get appName;

  /// No description provided for @tagline.
  ///
  /// In ru, this message translates to:
  /// **'ИИ-помощник студента и преподавателя'**
  String get tagline;

  /// No description provided for @next.
  ///
  /// In ru, this message translates to:
  /// **'Далее'**
  String get next;

  /// No description provided for @back.
  ///
  /// In ru, this message translates to:
  /// **'Назад'**
  String get back;

  /// No description provided for @cancel.
  ///
  /// In ru, this message translates to:
  /// **'Отмена'**
  String get cancel;

  /// No description provided for @save.
  ///
  /// In ru, this message translates to:
  /// **'Сохранить'**
  String get save;

  /// No description provided for @done.
  ///
  /// In ru, this message translates to:
  /// **'Готово'**
  String get done;

  /// No description provided for @retry.
  ///
  /// In ru, this message translates to:
  /// **'Повторить'**
  String get retry;

  /// No description provided for @delete.
  ///
  /// In ru, this message translates to:
  /// **'Удалить'**
  String get delete;

  /// No description provided for @rename.
  ///
  /// In ru, this message translates to:
  /// **'Переименовать'**
  String get rename;

  /// No description provided for @close.
  ///
  /// In ru, this message translates to:
  /// **'Закрыть'**
  String get close;

  /// No description provided for @copy.
  ///
  /// In ru, this message translates to:
  /// **'Копировать'**
  String get copy;

  /// No description provided for @copied.
  ///
  /// In ru, this message translates to:
  /// **'Скопировано'**
  String get copied;

  /// No description provided for @search.
  ///
  /// In ru, this message translates to:
  /// **'Поиск'**
  String get search;

  /// No description provided for @ok.
  ///
  /// In ru, this message translates to:
  /// **'Хорошо'**
  String get ok;

  /// No description provided for @loading.
  ///
  /// In ru, this message translates to:
  /// **'Загрузка...'**
  String get loading;

  /// No description provided for @send.
  ///
  /// In ru, this message translates to:
  /// **'Отправить'**
  String get send;

  /// No description provided for @stop.
  ///
  /// In ru, this message translates to:
  /// **'Остановить'**
  String get stop;

  /// No description provided for @welcomeTitle.
  ///
  /// In ru, this message translates to:
  /// **'Привет! Я Думыч'**
  String get welcomeTitle;

  /// No description provided for @welcomeBody.
  ///
  /// In ru, this message translates to:
  /// **'Отвечаю на вопросы текстом и голосом, знаю твоё расписание и разбираюсь в твоих методичках.'**
  String get welcomeBody;

  /// No description provided for @featureChat.
  ///
  /// In ru, this message translates to:
  /// **'Чат и голос: спроси \"Какая у меня следующая пара?\"'**
  String get featureChat;

  /// No description provided for @featureSchedule.
  ///
  /// In ru, this message translates to:
  /// **'Расписание группы, работает и без интернета'**
  String get featureSchedule;

  /// No description provided for @featureDocs.
  ///
  /// In ru, this message translates to:
  /// **'Ответы по PDF, DOCX и XLSX со ссылками на страницу'**
  String get featureDocs;

  /// No description provided for @featurePrivacy.
  ///
  /// In ru, this message translates to:
  /// **'Без телефона и почты: только псевдоним'**
  String get featurePrivacy;

  /// No description provided for @language.
  ///
  /// In ru, this message translates to:
  /// **'Язык'**
  String get language;

  /// No description provided for @languageSystem.
  ///
  /// In ru, this message translates to:
  /// **'Как в системе'**
  String get languageSystem;

  /// No description provided for @theme.
  ///
  /// In ru, this message translates to:
  /// **'Тема'**
  String get theme;

  /// No description provided for @themeSystem.
  ///
  /// In ru, this message translates to:
  /// **'Как в системе'**
  String get themeSystem;

  /// No description provided for @themeLight.
  ///
  /// In ru, this message translates to:
  /// **'Светлая'**
  String get themeLight;

  /// No description provided for @themeDark.
  ///
  /// In ru, this message translates to:
  /// **'Тёмная'**
  String get themeDark;

  /// No description provided for @haveAccount.
  ///
  /// In ru, this message translates to:
  /// **'У меня уже есть аккаунт'**
  String get haveAccount;

  /// No description provided for @start.
  ///
  /// In ru, this message translates to:
  /// **'Начать'**
  String get start;

  /// No description provided for @inviteTitle.
  ///
  /// In ru, this message translates to:
  /// **'Код приглашения'**
  String get inviteTitle;

  /// No description provided for @inviteHint.
  ///
  /// In ru, this message translates to:
  /// **'Код вида ABCD-EFGH выдают в деканате или куратор группы.'**
  String get inviteHint;

  /// No description provided for @inviteField.
  ///
  /// In ru, this message translates to:
  /// **'Код приглашения'**
  String get inviteField;

  /// No description provided for @inviteScan.
  ///
  /// In ru, this message translates to:
  /// **'Сканировать QR'**
  String get inviteScan;

  /// No description provided for @inviteNoCode.
  ///
  /// In ru, this message translates to:
  /// **'Где взять код?'**
  String get inviteNoCode;

  /// No description provided for @inviteNoCodeBody.
  ///
  /// In ru, this message translates to:
  /// **'Пока Думыч работает в пилоте, вход только по приглашениям. Спросите код у куратора группы или в деканате.'**
  String get inviteNoCodeBody;

  /// No description provided for @inviteFor.
  ///
  /// In ru, this message translates to:
  /// **'Код для: {tenant}'**
  String inviteFor(String tenant);

  /// No description provided for @roleStudent.
  ///
  /// In ru, this message translates to:
  /// **'студент'**
  String get roleStudent;

  /// No description provided for @roleTeacher.
  ///
  /// In ru, this message translates to:
  /// **'преподаватель'**
  String get roleTeacher;

  /// No description provided for @roleStaff.
  ///
  /// In ru, this message translates to:
  /// **'сотрудник'**
  String get roleStaff;

  /// No description provided for @registerTitle.
  ///
  /// In ru, this message translates to:
  /// **'Создание аккаунта'**
  String get registerTitle;

  /// No description provided for @nickname.
  ///
  /// In ru, this message translates to:
  /// **'Псевдоним'**
  String get nickname;

  /// No description provided for @nicknameHint.
  ///
  /// In ru, this message translates to:
  /// **'3-24 символа. Не используйте настоящее имя.'**
  String get nicknameHint;

  /// No description provided for @nicknameSuggest.
  ///
  /// In ru, this message translates to:
  /// **'Придумать'**
  String get nicknameSuggest;

  /// No description provided for @nicknameTaken.
  ///
  /// In ru, this message translates to:
  /// **'Этот псевдоним уже занят'**
  String get nicknameTaken;

  /// No description provided for @nicknameInvalid.
  ///
  /// In ru, this message translates to:
  /// **'Буквы, цифры, точка, дефис и подчёркивание, от 3 до 24 символов'**
  String get nicknameInvalid;

  /// No description provided for @nicknameLooksLikeName.
  ///
  /// In ru, this message translates to:
  /// **'Похоже на имя и фамилию. Лучше выбрать псевдоним, по которому вас не узнать.'**
  String get nicknameLooksLikeName;

  /// No description provided for @password.
  ///
  /// In ru, this message translates to:
  /// **'Пароль'**
  String get password;

  /// No description provided for @passwordRepeat.
  ///
  /// In ru, this message translates to:
  /// **'Повторите пароль'**
  String get passwordRepeat;

  /// No description provided for @passwordHint.
  ///
  /// In ru, this message translates to:
  /// **'Не меньше 10 символов'**
  String get passwordHint;

  /// No description provided for @passwordMismatch.
  ///
  /// In ru, this message translates to:
  /// **'Пароли не совпадают'**
  String get passwordMismatch;

  /// No description provided for @passwordWeak.
  ///
  /// In ru, this message translates to:
  /// **'Слабый'**
  String get passwordWeak;

  /// No description provided for @passwordFair.
  ///
  /// In ru, this message translates to:
  /// **'Средний'**
  String get passwordFair;

  /// No description provided for @passwordGood.
  ///
  /// In ru, this message translates to:
  /// **'Хороший'**
  String get passwordGood;

  /// No description provided for @passwordStrong.
  ///
  /// In ru, this message translates to:
  /// **'Сильный'**
  String get passwordStrong;

  /// No description provided for @createAccount.
  ///
  /// In ru, this message translates to:
  /// **'Создать аккаунт'**
  String get createAccount;

  /// No description provided for @recoveryTitle.
  ///
  /// In ru, this message translates to:
  /// **'Код восстановления'**
  String get recoveryTitle;

  /// No description provided for @recoveryBody.
  ///
  /// In ru, this message translates to:
  /// **'Это единственный способ восстановить доступ, если забудете пароль: почты и телефона у нас нет. Сохраните код в надёжном месте.'**
  String get recoveryBody;

  /// No description provided for @recoverySaveFile.
  ///
  /// In ru, this message translates to:
  /// **'Сохранить в файл'**
  String get recoverySaveFile;

  /// No description provided for @recoveryShare.
  ///
  /// In ru, this message translates to:
  /// **'Поделиться'**
  String get recoveryShare;

  /// No description provided for @recoveryConfirm.
  ///
  /// In ru, this message translates to:
  /// **'Я сохранил код восстановления'**
  String get recoveryConfirm;

  /// No description provided for @termsTitle.
  ///
  /// In ru, this message translates to:
  /// **'Правила и данные'**
  String get termsTitle;

  /// No description provided for @termsAccept.
  ///
  /// In ru, this message translates to:
  /// **'Принимаю правила'**
  String get termsAccept;

  /// No description provided for @termsOpen.
  ///
  /// In ru, this message translates to:
  /// **'Пользовательское соглашение'**
  String get termsOpen;

  /// No description provided for @dataOpen.
  ///
  /// In ru, this message translates to:
  /// **'Какие данные мы обрабатываем'**
  String get dataOpen;

  /// No description provided for @groupTitle.
  ///
  /// In ru, this message translates to:
  /// **'Ваша группа'**
  String get groupTitle;

  /// No description provided for @groupBody.
  ///
  /// In ru, this message translates to:
  /// **'Группа нужна для расписания. Её можно хранить на сервере (тогда ассистент знает её на всех устройствах) или только на этом устройстве.'**
  String get groupBody;

  /// No description provided for @groupSearch.
  ///
  /// In ru, this message translates to:
  /// **'Найти группу'**
  String get groupSearch;

  /// No description provided for @groupOnServer.
  ///
  /// In ru, this message translates to:
  /// **'Хранить на сервере'**
  String get groupOnServer;

  /// No description provided for @groupOnDevice.
  ///
  /// In ru, this message translates to:
  /// **'Только на этом устройстве'**
  String get groupOnDevice;

  /// No description provided for @groupLater.
  ///
  /// In ru, this message translates to:
  /// **'Выбрать позже'**
  String get groupLater;

  /// No description provided for @subgroup.
  ///
  /// In ru, this message translates to:
  /// **'Подгруппа'**
  String get subgroup;

  /// No description provided for @subgroupAny.
  ///
  /// In ru, this message translates to:
  /// **'Без подгруппы'**
  String get subgroupAny;

  /// No description provided for @loginTitle.
  ///
  /// In ru, this message translates to:
  /// **'Вход'**
  String get loginTitle;

  /// No description provided for @login.
  ///
  /// In ru, this message translates to:
  /// **'Войти'**
  String get login;

  /// No description provided for @forgotPassword.
  ///
  /// In ru, this message translates to:
  /// **'Забыли пароль?'**
  String get forgotPassword;

  /// No description provided for @recoverTitle.
  ///
  /// In ru, this message translates to:
  /// **'Восстановление доступа'**
  String get recoverTitle;

  /// No description provided for @recoveryCode.
  ///
  /// In ru, this message translates to:
  /// **'Код восстановления'**
  String get recoveryCode;

  /// No description provided for @newPassword.
  ///
  /// In ru, this message translates to:
  /// **'Новый пароль'**
  String get newPassword;

  /// No description provided for @recover.
  ///
  /// In ru, this message translates to:
  /// **'Восстановить'**
  String get recover;

  /// No description provided for @newRecoveryCode.
  ///
  /// In ru, this message translates to:
  /// **'Новый код восстановления'**
  String get newRecoveryCode;

  /// No description provided for @newRecoveryCodeBody.
  ///
  /// In ru, this message translates to:
  /// **'Старый код больше не работает. Сохраните новый.'**
  String get newRecoveryCodeBody;

  /// No description provided for @qrLoginTitle.
  ///
  /// In ru, this message translates to:
  /// **'Вход по QR с телефона'**
  String get qrLoginTitle;

  /// No description provided for @qrLoginBody.
  ///
  /// In ru, this message translates to:
  /// **'Откройте Думыч на телефоне: Настройки, Войти на ПК, и наведите камеру на код.'**
  String get qrLoginBody;

  /// No description provided for @qrApproveTitle.
  ///
  /// In ru, this message translates to:
  /// **'Войти на компьютере?'**
  String get qrApproveTitle;

  /// No description provided for @qrApproveBody.
  ///
  /// In ru, this message translates to:
  /// **'Подтвердите, только если код показан на вашем компьютере.'**
  String get qrApproveBody;

  /// No description provided for @qrApprove.
  ///
  /// In ru, this message translates to:
  /// **'Войти'**
  String get qrApprove;

  /// No description provided for @signInOnPc.
  ///
  /// In ru, this message translates to:
  /// **'Войти на ПК'**
  String get signInOnPc;

  /// No description provided for @tabChat.
  ///
  /// In ru, this message translates to:
  /// **'Чат'**
  String get tabChat;

  /// No description provided for @tabSchedule.
  ///
  /// In ru, this message translates to:
  /// **'Расписание'**
  String get tabSchedule;

  /// No description provided for @tabDocuments.
  ///
  /// In ru, this message translates to:
  /// **'Документы'**
  String get tabDocuments;

  /// No description provided for @tabSettings.
  ///
  /// In ru, this message translates to:
  /// **'Настройки'**
  String get tabSettings;

  /// No description provided for @tabMore.
  ///
  /// In ru, this message translates to:
  /// **'Ещё'**
  String get tabMore;

  /// No description provided for @chats.
  ///
  /// In ru, this message translates to:
  /// **'Чаты'**
  String get chats;

  /// No description provided for @newChat.
  ///
  /// In ru, this message translates to:
  /// **'Новый чат'**
  String get newChat;

  /// No description provided for @incognito.
  ///
  /// In ru, this message translates to:
  /// **'Инкогнито'**
  String get incognito;

  /// No description provided for @incognitoHint.
  ///
  /// In ru, this message translates to:
  /// **'Этот чат не сохраняется на сервере и исчезнет после закрытия.'**
  String get incognitoHint;

  /// No description provided for @chatEmpty.
  ///
  /// In ru, this message translates to:
  /// **'Спросите что угодно: объясню тему, помогу с задачей, найду ответ в методичке.'**
  String get chatEmpty;

  /// No description provided for @chatSuggest1.
  ///
  /// In ru, this message translates to:
  /// **'Какая у меня следующая пара?'**
  String get chatSuggest1;

  /// No description provided for @chatSuggest2.
  ///
  /// In ru, this message translates to:
  /// **'Объясни производную простыми словами'**
  String get chatSuggest2;

  /// No description provided for @chatSuggest3.
  ///
  /// In ru, this message translates to:
  /// **'Когда экзамен по физике?'**
  String get chatSuggest3;

  /// No description provided for @messageHint.
  ///
  /// In ru, this message translates to:
  /// **'Сообщение'**
  String get messageHint;

  /// No description provided for @holdToTalk.
  ///
  /// In ru, this message translates to:
  /// **'Удерживайте, чтобы говорить'**
  String get holdToTalk;

  /// No description provided for @tapToTalk.
  ///
  /// In ru, this message translates to:
  /// **'Нажмите, чтобы говорить'**
  String get tapToTalk;

  /// No description provided for @listening.
  ///
  /// In ru, this message translates to:
  /// **'Слушаю...'**
  String get listening;

  /// No description provided for @thinking.
  ///
  /// In ru, this message translates to:
  /// **'Думаю...'**
  String get thinking;

  /// No description provided for @speaking.
  ///
  /// In ru, this message translates to:
  /// **'Отвечаю'**
  String get speaking;

  /// No description provided for @readAloud.
  ///
  /// In ru, this message translates to:
  /// **'Читать ответы вслух'**
  String get readAloud;

  /// No description provided for @speak.
  ///
  /// In ru, this message translates to:
  /// **'Озвучить'**
  String get speak;

  /// No description provided for @attachDocument.
  ///
  /// In ru, this message translates to:
  /// **'Спросить по документу'**
  String get attachDocument;

  /// No description provided for @toolSchedule.
  ///
  /// In ru, this message translates to:
  /// **'Смотрю расписание'**
  String get toolSchedule;

  /// No description provided for @toolDocuments.
  ///
  /// In ru, this message translates to:
  /// **'Ищу в документах'**
  String get toolDocuments;

  /// No description provided for @toolGeneric.
  ///
  /// In ru, this message translates to:
  /// **'Работаю с данными вуза'**
  String get toolGeneric;

  /// No description provided for @sources.
  ///
  /// In ru, this message translates to:
  /// **'Источники'**
  String get sources;

  /// No description provided for @page.
  ///
  /// In ru, this message translates to:
  /// **'стр. {page}'**
  String page(String page);

  /// No description provided for @sheet.
  ///
  /// In ru, this message translates to:
  /// **'лист {sheet}'**
  String sheet(String sheet);

  /// No description provided for @feedbackGood.
  ///
  /// In ru, this message translates to:
  /// **'Хороший ответ'**
  String get feedbackGood;

  /// No description provided for @feedbackBad.
  ///
  /// In ru, this message translates to:
  /// **'Плохой ответ'**
  String get feedbackBad;

  /// No description provided for @feedbackTitle.
  ///
  /// In ru, this message translates to:
  /// **'Что не так?'**
  String get feedbackTitle;

  /// No description provided for @feedbackWrong.
  ///
  /// In ru, this message translates to:
  /// **'Ответ неверный'**
  String get feedbackWrong;

  /// No description provided for @feedbackNoSource.
  ///
  /// In ru, this message translates to:
  /// **'Нет ссылки на источник'**
  String get feedbackNoSource;

  /// No description provided for @feedbackVoice.
  ///
  /// In ru, this message translates to:
  /// **'Плохо распознал или озвучил'**
  String get feedbackVoice;

  /// No description provided for @feedbackOther.
  ///
  /// In ru, this message translates to:
  /// **'Другое'**
  String get feedbackOther;

  /// No description provided for @feedbackComment.
  ///
  /// In ru, this message translates to:
  /// **'Комментарий (необязательно)'**
  String get feedbackComment;

  /// No description provided for @feedbackShare.
  ///
  /// In ru, this message translates to:
  /// **'Приложить вопрос и ответ, чтобы команда разобралась'**
  String get feedbackShare;

  /// No description provided for @feedbackThanks.
  ///
  /// In ru, this message translates to:
  /// **'Спасибо за оценку!'**
  String get feedbackThanks;

  /// No description provided for @aiNotice.
  ///
  /// In ru, this message translates to:
  /// **'Ответы генерирует ИИ и могут содержать ошибки.'**
  String get aiNotice;

  /// No description provided for @today.
  ///
  /// In ru, this message translates to:
  /// **'Сегодня'**
  String get today;

  /// No description provided for @tomorrow.
  ///
  /// In ru, this message translates to:
  /// **'Завтра'**
  String get tomorrow;

  /// No description provided for @week.
  ///
  /// In ru, this message translates to:
  /// **'Неделя'**
  String get week;

  /// No description provided for @day.
  ///
  /// In ru, this message translates to:
  /// **'День'**
  String get day;

  /// No description provided for @nowLesson.
  ///
  /// In ru, this message translates to:
  /// **'Сейчас'**
  String get nowLesson;

  /// No description provided for @nextLesson.
  ///
  /// In ru, this message translates to:
  /// **'Далее'**
  String get nextLesson;

  /// No description provided for @noLessons.
  ///
  /// In ru, this message translates to:
  /// **'Занятий нет'**
  String get noLessons;

  /// No description provided for @noGroup.
  ///
  /// In ru, this message translates to:
  /// **'Группа не выбрана'**
  String get noGroup;

  /// No description provided for @chooseGroup.
  ///
  /// In ru, this message translates to:
  /// **'Выбрать группу'**
  String get chooseGroup;

  /// No description provided for @offlineUpdated.
  ///
  /// In ru, this message translates to:
  /// **'Без сети. Обновлено {time}'**
  String offlineUpdated(String time);

  /// No description provided for @cancelled.
  ///
  /// In ru, this message translates to:
  /// **'Отменено'**
  String get cancelled;

  /// No description provided for @room.
  ///
  /// In ru, this message translates to:
  /// **'ауд. {room}'**
  String room(String room);

  /// No description provided for @teacherMode.
  ///
  /// In ru, this message translates to:
  /// **'Расписание преподавателя'**
  String get teacherMode;

  /// No description provided for @teacherName.
  ///
  /// In ru, this message translates to:
  /// **'Ваше имя как в расписании'**
  String get teacherName;

  /// No description provided for @teacherNameHint.
  ///
  /// In ru, this message translates to:
  /// **'Хранится только на этом устройстве, на сервер уходит лишь обезличенный ключ.'**
  String get teacherNameHint;

  /// No description provided for @kindLecture.
  ///
  /// In ru, this message translates to:
  /// **'Лекция'**
  String get kindLecture;

  /// No description provided for @kindPractice.
  ///
  /// In ru, this message translates to:
  /// **'Практика'**
  String get kindPractice;

  /// No description provided for @kindLab.
  ///
  /// In ru, this message translates to:
  /// **'Лабораторная'**
  String get kindLab;

  /// No description provided for @kindExam.
  ///
  /// In ru, this message translates to:
  /// **'Экзамен'**
  String get kindExam;

  /// No description provided for @kindCredit.
  ///
  /// In ru, this message translates to:
  /// **'Зачёт'**
  String get kindCredit;

  /// No description provided for @kindConsultation.
  ///
  /// In ru, this message translates to:
  /// **'Консультация'**
  String get kindConsultation;

  /// No description provided for @kindOther.
  ///
  /// In ru, this message translates to:
  /// **'Занятие'**
  String get kindOther;

  /// No description provided for @documents.
  ///
  /// In ru, this message translates to:
  /// **'Документы'**
  String get documents;

  /// No description provided for @upload.
  ///
  /// In ru, this message translates to:
  /// **'Загрузить'**
  String get upload;

  /// No description provided for @documentsEmpty.
  ///
  /// In ru, this message translates to:
  /// **'Загрузите методичку, конспект или таблицу, и я буду отвечать по ним со ссылками на страницы.'**
  String get documentsEmpty;

  /// No description provided for @docLimits.
  ///
  /// In ru, this message translates to:
  /// **'PDF, DOCX, XLSX, PPTX до 20 МБ'**
  String get docLimits;

  /// No description provided for @statusProcessing.
  ///
  /// In ru, this message translates to:
  /// **'Обрабатывается'**
  String get statusProcessing;

  /// No description provided for @statusReady.
  ///
  /// In ru, this message translates to:
  /// **'Готов'**
  String get statusReady;

  /// No description provided for @statusFailed.
  ///
  /// In ru, this message translates to:
  /// **'Ошибка'**
  String get statusFailed;

  /// No description provided for @askDocument.
  ///
  /// In ru, this message translates to:
  /// **'Спросить по документу'**
  String get askDocument;

  /// No description provided for @deleteDocument.
  ///
  /// In ru, this message translates to:
  /// **'Удалить документ?'**
  String get deleteDocument;

  /// No description provided for @deleteDocumentBody.
  ///
  /// In ru, this message translates to:
  /// **'Файл и его индекс удалятся с сервера.'**
  String get deleteDocumentBody;

  /// No description provided for @pages.
  ///
  /// In ru, this message translates to:
  /// **'{count} стр.'**
  String pages(int count);

  /// No description provided for @sourceTitle.
  ///
  /// In ru, this message translates to:
  /// **'Фрагмент документа'**
  String get sourceTitle;

  /// No description provided for @settings.
  ///
  /// In ru, this message translates to:
  /// **'Настройки'**
  String get settings;

  /// No description provided for @appearance.
  ///
  /// In ru, this message translates to:
  /// **'Оформление'**
  String get appearance;

  /// No description provided for @voice.
  ///
  /// In ru, this message translates to:
  /// **'Голос'**
  String get voice;

  /// No description provided for @speechRate.
  ///
  /// In ru, this message translates to:
  /// **'Скорость речи'**
  String get speechRate;

  /// No description provided for @pttMode.
  ///
  /// In ru, this message translates to:
  /// **'Режим кнопки микрофона'**
  String get pttMode;

  /// No description provided for @pttHold.
  ///
  /// In ru, this message translates to:
  /// **'Удерживать'**
  String get pttHold;

  /// No description provided for @pttToggle.
  ///
  /// In ru, this message translates to:
  /// **'Нажать и ещё раз нажать'**
  String get pttToggle;

  /// No description provided for @privacy.
  ///
  /// In ru, this message translates to:
  /// **'Приватность'**
  String get privacy;

  /// No description provided for @historyRetention.
  ///
  /// In ru, this message translates to:
  /// **'Хранить историю чатов'**
  String get historyRetention;

  /// No description provided for @days.
  ///
  /// In ru, this message translates to:
  /// **'{count} дн.'**
  String days(int count);

  /// No description provided for @dontStore.
  ///
  /// In ru, this message translates to:
  /// **'Не хранить'**
  String get dontStore;

  /// No description provided for @incognitoDefault.
  ///
  /// In ru, this message translates to:
  /// **'Новые чаты в режиме инкогнито'**
  String get incognitoDefault;

  /// No description provided for @account.
  ///
  /// In ru, this message translates to:
  /// **'Аккаунт'**
  String get account;

  /// No description provided for @changePassword.
  ///
  /// In ru, this message translates to:
  /// **'Сменить пароль'**
  String get changePassword;

  /// No description provided for @oldPassword.
  ///
  /// In ru, this message translates to:
  /// **'Текущий пароль'**
  String get oldPassword;

  /// No description provided for @sessions.
  ///
  /// In ru, this message translates to:
  /// **'Устройства'**
  String get sessions;

  /// No description provided for @thisDevice.
  ///
  /// In ru, this message translates to:
  /// **'Это устройство'**
  String get thisDevice;

  /// No description provided for @logout.
  ///
  /// In ru, this message translates to:
  /// **'Выйти'**
  String get logout;

  /// No description provided for @deleteAccount.
  ///
  /// In ru, this message translates to:
  /// **'Удалить аккаунт'**
  String get deleteAccount;

  /// No description provided for @deleteAccountBody.
  ///
  /// In ru, this message translates to:
  /// **'Чаты, документы и настройки удалятся сразу, из резервных копий в течение 30 дней. Отменить нельзя.'**
  String get deleteAccountBody;

  /// No description provided for @confirmPassword.
  ///
  /// In ru, this message translates to:
  /// **'Введите пароль для подтверждения'**
  String get confirmPassword;

  /// No description provided for @about.
  ///
  /// In ru, this message translates to:
  /// **'О приложении'**
  String get about;

  /// No description provided for @version.
  ///
  /// In ru, this message translates to:
  /// **'Версия {version}'**
  String version(String version);

  /// No description provided for @reportProblem.
  ///
  /// In ru, this message translates to:
  /// **'Сообщить о проблеме'**
  String get reportProblem;

  /// No description provided for @legal.
  ///
  /// In ru, this message translates to:
  /// **'Документы'**
  String get legal;

  /// No description provided for @updateAvailable.
  ///
  /// In ru, this message translates to:
  /// **'Доступна версия {version}'**
  String updateAvailable(String version);

  /// No description provided for @updateInstall.
  ///
  /// In ru, this message translates to:
  /// **'Обновить'**
  String get updateInstall;

  /// No description provided for @errNetwork.
  ///
  /// In ru, this message translates to:
  /// **'Нет связи с сервером. Проверьте интернет.'**
  String get errNetwork;

  /// No description provided for @errBadCredentials.
  ///
  /// In ru, this message translates to:
  /// **'Неверный псевдоним или пароль'**
  String get errBadCredentials;

  /// No description provided for @errRateLimited.
  ///
  /// In ru, this message translates to:
  /// **'Слишком много попыток. Подождите немного.'**
  String get errRateLimited;

  /// No description provided for @errInviteInvalid.
  ///
  /// In ru, this message translates to:
  /// **'Код не найден. Проверьте, нет ли опечатки.'**
  String get errInviteInvalid;

  /// No description provided for @errInviteUsed.
  ///
  /// In ru, this message translates to:
  /// **'Этот код уже использован'**
  String get errInviteUsed;

  /// No description provided for @errInviteExpired.
  ///
  /// In ru, this message translates to:
  /// **'Срок действия кода истёк'**
  String get errInviteExpired;

  /// No description provided for @errInviteRevoked.
  ///
  /// In ru, this message translates to:
  /// **'Код отозван'**
  String get errInviteRevoked;

  /// No description provided for @errPasswordWeak.
  ///
  /// In ru, this message translates to:
  /// **'Пароль слишком простой'**
  String get errPasswordWeak;

  /// No description provided for @errBadRecovery.
  ///
  /// In ru, this message translates to:
  /// **'Неверный псевдоним или код восстановления'**
  String get errBadRecovery;

  /// No description provided for @errFileTooLarge.
  ///
  /// In ru, this message translates to:
  /// **'Файл больше 20 МБ'**
  String get errFileTooLarge;

  /// No description provided for @errUnsupportedType.
  ///
  /// In ru, this message translates to:
  /// **'Поддерживаются PDF, DOCX, XLSX и PPTX'**
  String get errUnsupportedType;

  /// No description provided for @errDocumentsLimit.
  ///
  /// In ru, this message translates to:
  /// **'Достигнут лимит документов'**
  String get errDocumentsLimit;

  /// No description provided for @errNoSpeech.
  ///
  /// In ru, this message translates to:
  /// **'Не расслышал. Попробуйте ещё раз.'**
  String get errNoSpeech;

  /// No description provided for @errMicPermission.
  ///
  /// In ru, this message translates to:
  /// **'Нет доступа к микрофону. Разрешите его в настройках.'**
  String get errMicPermission;

  /// No description provided for @errLlm.
  ///
  /// In ru, this message translates to:
  /// **'Ассистент сейчас недоступен. Попробуйте позже.'**
  String get errLlm;

  /// No description provided for @errHistoryDisabled.
  ///
  /// In ru, this message translates to:
  /// **'История отключена в настройках, чат откроется в режиме инкогнито.'**
  String get errHistoryDisabled;

  /// No description provided for @errGeneric.
  ///
  /// In ru, this message translates to:
  /// **'Что-то пошло не так'**
  String get errGeneric;

  /// No description provided for @errBlocked.
  ///
  /// In ru, this message translates to:
  /// **'Аккаунт заблокирован'**
  String get errBlocked;

  /// No description provided for @docFailed_virus_found.
  ///
  /// In ru, this message translates to:
  /// **'Файл не прошёл антивирусную проверку'**
  String get docFailed_virus_found;

  /// No description provided for @docFailed_needs_ocr.
  ///
  /// In ru, this message translates to:
  /// **'Похоже на скан без текста'**
  String get docFailed_needs_ocr;

  /// No description provided for @docFailed_too_many_pages.
  ///
  /// In ru, this message translates to:
  /// **'Больше 300 страниц'**
  String get docFailed_too_many_pages;

  /// No description provided for @docFailed_empty_document.
  ///
  /// In ru, this message translates to:
  /// **'В документе нет текста'**
  String get docFailed_empty_document;

  /// No description provided for @docFailed_pdf_encrypted.
  ///
  /// In ru, this message translates to:
  /// **'PDF защищён паролем'**
  String get docFailed_pdf_encrypted;

  /// No description provided for @hotkeyHint.
  ///
  /// In ru, this message translates to:
  /// **'Удерживайте Ctrl+Пробел, чтобы говорить. Ctrl+M: микрофон, Ctrl+N: новый чат'**
  String get hotkeyHint;
}

class _SDelegate extends LocalizationsDelegate<S> {
  const _SDelegate();

  @override
  Future<S> load(Locale locale) {
    return SynchronousFuture<S>(lookupS(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'ru'].contains(locale.languageCode);

  @override
  bool shouldReload(_SDelegate old) => false;
}

S lookupS(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return SEn();
    case 'ru':
      return SRu();
  }

  throw FlutterError(
    'S.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
