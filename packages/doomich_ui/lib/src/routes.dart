/// Пути экранов. Оболочки приложений (mobile, desktop) регистрируют их в своём go_router.
class Routes {
  static const welcome = '/welcome';
  static const invite = '/invite';
  static const register = '/register';
  static const recoveryCode = '/recovery-code';
  static const terms = '/terms';
  static const group = '/group';
  static const login = '/login';
  static const recover = '/recover';
  static const qrLogin = '/qr-login';

  static const chats = '/chats';
  static String chat(String id) => '/chats/$id';
  static const incognito = '/chats/incognito';
  static const schedule = '/schedule';
  static const documents = '/documents';
  static String source(String doc, String chunk) => '/documents/$doc/chunks/$chunk';
  static const settings = '/settings';
  static const sessions = '/settings/sessions';
  static const legal = '/settings/legal';

  static const onboarding = {welcome, invite, register, recoveryCode, terms, group, login, recover, qrLogin};
}
