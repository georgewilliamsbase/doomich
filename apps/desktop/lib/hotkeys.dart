import 'package:doomich_core/doomich_core.dart';
import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hotkey_manager/hotkey_manager.dart';

/// Голосовой ввод удержанием Ctrl+Пробел, в том числе когда окно не в фокусе (Windows, Linux X11).
class GlobalHotkeys extends ConsumerStatefulWidget {
  const GlobalHotkeys({super.key, required this.child});

  final Widget child;

  /// Чат, в который пойдёт голосовой вопрос (последний открытый)
  static String? activeChat;

  static void setActive(String? chatId) => activeChat = chatId;

  @override
  ConsumerState<GlobalHotkeys> createState() => _GlobalHotkeysState();
}

class _GlobalHotkeysState extends ConsumerState<GlobalHotkeys> {
  String? get activeChat => GlobalHotkeys.activeChat;

  final _ptt = HotKey(key: PhysicalKeyboardKey.space, modifiers: [HotKeyModifier.control]);

  @override
  void initState() {
    super.initState();
    _register();
  }

  Future<void> _register() async {
    try {
      await hotKeyManager.register(
        _ptt,
        keyDownHandler: (_) => ref.read(voiceProvider.notifier).listen(chatId: activeChat),
        keyUpHandler: (_) => ref.read(voiceProvider.notifier).send(),
      );
    } catch (_) {
      // Сочетание занято другим приложением или окружение его не поддерживает
    }
  }

  @override
  void dispose() {
    hotKeyManager.unregister(_ptt);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
