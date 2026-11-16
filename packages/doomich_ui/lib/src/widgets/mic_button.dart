import 'package:doomich_core/doomich_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../strings.dart';

/// Кнопка "нажми и говори". Два режима: удерживать (по умолчанию) или нажать для старта и ещё раз для отправки.
/// Свайп влево во время удержания отменяет запись.
class MicButton extends ConsumerStatefulWidget {
  const MicButton({super.key, this.chatId, this.size = 48});

  final String? chatId;
  final double size;

  @override
  ConsumerState<MicButton> createState() => _MicButtonState();
}

class _MicButtonState extends ConsumerState<MicButton> {
  double _dragDx = 0;

  VoiceController get _voice => ref.read(voiceProvider.notifier);

  Future<void> _start() async {
    _dragDx = 0;
    await _voice.listen(chatId: widget.chatId);
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(voiceProvider);
    final hold = ref.watch(settingsProvider.select((s) => s.holdToTalk));
    final scheme = Theme.of(context).colorScheme;
    final listening = state.phase == VoicePhase.listening;
    final busy = state.phase == VoicePhase.thinking || state.phase == VoicePhase.connecting;
    final speaking = state.phase == VoicePhase.speaking;
    final s = context.s;

    final icon = speaking ? Icons.stop : (listening ? Icons.mic : Icons.mic_none);
    final button = AnimatedContainer(
      duration: const Duration(milliseconds: 120),
      width: widget.size + (listening ? 12 * state.level : 0),
      height: widget.size + (listening ? 12 * state.level : 0),
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: listening ? scheme.error : (speaking ? scheme.tertiary : scheme.primary),
      ),
      child: busy
          ? Padding(padding: const EdgeInsets.all(14), child: CircularProgressIndicator(strokeWidth: 2.5,
              color: scheme.onPrimary))
          : Icon(icon, color: scheme.onPrimary),
    );

    final tooltip = hold ? s.holdToTalk : s.tapToTalk;
    if (speaking) {
      return Tooltip(message: s.stop, child: InkResponse(onTap: _voice.stopSpeaking, child: button));
    }
    if (!hold) {
      return Tooltip(
        message: tooltip,
        child: Semantics(
          button: true,
          label: tooltip,
          child: InkResponse(onTap: listening ? _voice.send : (busy ? _voice.cancel : _start), child: button),
        ),
      );
    }
    return Tooltip(
      message: tooltip,
      child: Semantics(
        button: true,
        label: tooltip,
        // Для экранного диктора удержание неудобно: обычное нажатие работает как переключатель
        onTap: listening ? _voice.send : _start,
        child: GestureDetector(
          onLongPressStart: (_) => _start(),
          onLongPressMoveUpdate: (d) => _dragDx = d.offsetFromOrigin.dx,
          onLongPressEnd: (_) => _dragDx < -60 ? _voice.cancel() : _voice.send(),
          onTap: listening ? _voice.send : (busy ? _voice.cancel : null),
          child: button,
        ),
      ),
    );
  }
}
