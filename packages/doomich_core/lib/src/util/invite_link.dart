/// Разбор кода приглашения из QR или ссылки: doomich://invite/ABCD-EFGH?server=https://...
class InviteLink {
  const InviteLink(this.code, {this.server});

  final String code;
  final String? server;

  static final _code = RegExp(r'([A-Za-zА-Яа-я0-9]{4})-?([A-Za-zА-Яа-я0-9]{4})');

  static InviteLink? parse(String raw) {
    final text = raw.trim();
    final uri = Uri.tryParse(text);
    if (uri != null && uri.scheme == 'doomich' && uri.host == 'invite' && uri.pathSegments.isNotEmpty) {
      final server = uri.queryParameters['server'];
      return InviteLink(_normalize(uri.pathSegments.first), server: _safeServer(server));
    }
    final m = _code.firstMatch(text);
    if (m == null) return null;
    return InviteLink(_normalize('${m.group(1)}${m.group(2)}'));
  }

  static String _normalize(String s) {
    const lookalike = {'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H', 'Р': 'P', 'С': 'C', 'Т': 'T',
      'У': 'Y', 'Х': 'X'};
    final up = s.toUpperCase().replaceAll('-', '').split('').map((c) => lookalike[c] ?? c).join();
    return up.length == 8 ? '${up.substring(0, 4)}-${up.substring(4)}' : up;
  }

  /// Чужой сервер принимаем только по https (кроме локальной разработки).
  static String? _safeServer(String? s) {
    if (s == null || s.isEmpty) return null;
    final u = Uri.tryParse(s);
    if (u == null) return null;
    if (u.scheme == 'https') return s;
    if (u.scheme == 'http' && (u.host == 'localhost' || u.host == '10.0.2.2' || u.host.startsWith('192.168.'))) {
      return s;
    }
    return null;
  }
}
