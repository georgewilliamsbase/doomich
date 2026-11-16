import 'dart:math';

/// Генератор псевдонимов вида "ТихийЕнот42". Выбирается на устройстве,
/// сервер только проверяет, что такой ещё не занят.
class PseudonymGenerator {
  PseudonymGenerator([Random? random]) : _r = random ?? Random.secure();

  final Random _r;

  static const _adjRu = [
    'Тихий', 'Быстрый', 'Смелый', 'Мудрый', 'Весёлый', 'Ловкий', 'Добрый', 'Яркий', 'Спокойный', 'Звёздный',
    'Северный', 'Лунный', 'Бодрый', 'Хитрый', 'Зоркий', 'Сонный', 'Снежный', 'Рыжий', 'Пушистый', 'Отважный',
  ];
  static const _nounRu = [
    'Енот', 'Филин', 'Ёж', 'Барсук', 'Лис', 'Кот', 'Бобр', 'Тюлень', 'Пингвин', 'Сокол', 'Медведь', 'Волк',
    'Дельфин', 'Кит', 'Хомяк', 'Олень', 'Лемур', 'Панда', 'Тигр', 'Сыч',
  ];
  static const _adjEn = ['Quiet', 'Swift', 'Brave', 'Wise', 'Happy', 'Clever', 'Kind', 'Bright', 'Calm', 'Starry'];
  static const _nounEn = ['Raccoon', 'Owl', 'Hedgehog', 'Badger', 'Fox', 'Cat', 'Beaver', 'Seal', 'Penguin', 'Falcon'];

  String next({String lang = 'ru'}) {
    final adj = lang == 'en' ? _adjEn : _adjRu;
    final noun = lang == 'en' ? _nounEn : _nounRu;
    return '${adj[_r.nextInt(adj.length)]}${noun[_r.nextInt(noun.length)]}${10 + _r.nextInt(90)}';
  }

  List<String> suggestions({int count = 4, String lang = 'ru'}) {
    final out = <String>{};
    while (out.length < count) {
      out.add(next(lang: lang));
    }
    return out.toList();
  }
}

/// Проверки, совпадающие с серверными (services/api, accounts/service.py).
class LoginRules {
  static final _format = RegExp(r'^[0-9A-Za-zА-Яа-яЁё][0-9A-Za-zА-Яа-яЁё_.\-]{2,23}$');
  static final _words = RegExp(r'[А-ЯЁA-Z]?[а-яёa-z]+');
  static const _surnameSuffixes = ['ов', 'ев', 'ин', 'ын', 'ский', 'цкий', 'ова', 'ева', 'ина', 'ына', 'ская',
    'цкая', 'енко', 'ук', 'юк', 'швили', 'дзе', 'ян', 'ич'];
  static const _firstNames = {
    'александр', 'алексей', 'андрей', 'анна', 'анастасия', 'дмитрий', 'екатерина', 'елена', 'иван', 'мария',
    'михаил', 'наталья', 'ольга', 'сергей', 'татьяна', 'юлия', 'артем', 'дарья', 'максим', 'никита', 'полина',
    'софия', 'кирилл', 'виктория', 'егор', 'алина', 'илья', 'ксения', 'владимир', 'павел', 'роман', 'денис',
    'евгений', 'николай', 'ирина', 'светлана', 'марина', 'валерия', 'арина',
  };

  static bool isValid(String login) => _format.hasMatch(login.trim());

  /// Подсказка "похоже на имя и фамилию". Только предупреждение, не запрет.
  static bool looksLikeName(String login) => warning(login) != null;

  /// looks_like_name, looks_like_email, looks_like_phone или null.
  static String? warning(String login) {
    final s = login.trim();
    final low = s.toLowerCase().replaceAll('ё', 'е');
    if (s.contains('@')) return 'looks_like_email';
    if (RegExp(r'\d{10,}').hasMatch(low)) return 'looks_like_phone';
    final raw = _words.allMatches(s).map((m) => m.group(0)!).toList();
    final words = raw.map((w) => w.toLowerCase().replaceAll('ё', 'е')).toList();
    if (words.any(_firstNames.contains)) return 'looks_like_name';
    if (words.length == 1 && _firstNames.any((n) => low.startsWith(n) && low.length > n.length + 2)) {
      return 'looks_like_name';
    }
    final capitalized = raw.where((w) => w[0] != w[0].toLowerCase()).toList();
    final hasDigits = RegExp(r'\d').hasMatch(s);
    if (!hasDigits &&
        capitalized.length >= 2 &&
        capitalized.any((w) => w.length >= 4 && _surnameSuffixes.any((x) => w.toLowerCase().endsWith(x)))) {
      return 'looks_like_name';
    }
    return null;
  }
}
