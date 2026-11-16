/// Оценка стойкости пароля для индикатора при регистрации (0..4).
/// Сервер дополнительно проверяет длину и словарь частых паролей.
int passwordScore(String password, {String? login}) {
  if (password.length < 10) return 0;
  var classes = 0;
  if (RegExp(r'[a-zа-яё]').hasMatch(password)) classes++;
  if (RegExp(r'[A-ZА-ЯЁ]').hasMatch(password)) classes++;
  if (RegExp(r'\d').hasMatch(password)) classes++;
  if (RegExp(r'[^\w\s]|_').hasMatch(password)) classes++;
  var score = 1;
  if (password.length >= 12) score++;
  if (password.length >= 16) score++;
  if (classes >= 3) score++;
  if (password.toSet().length < 5) score = 1;
  if (login != null && login.isNotEmpty && password.toLowerCase().contains(login.toLowerCase())) score = 1;
  if (_common.contains(password.toLowerCase())) score = 0;
  return score.clamp(0, 4);
}

extension on String {
  Set<String> toSet() => split('').toSet();
}

const _common = {
  '1234567890', '0123456789', 'qwertyuiop', 'password123', 'qwerty1234', '1q2w3e4r5t', 'йцукенгшщз', 'пароль1234',
};
