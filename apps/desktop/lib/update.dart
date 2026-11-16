import 'dart:io';

import 'package:doomich_core/doomich_core.dart';
import 'package:doomich_ui/doomich_ui.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Самообновление ПК-версии: скачиваем установщик, сверяем SHA-256 и запускаем.
/// На Windows это установщик Inno Setup, на Linux AppImage заменяется на месте,
/// для deb и rpm показываем команду обновления.
class UpdateScreen extends ConsumerStatefulWidget {
  const UpdateScreen({super.key});

  @override
  ConsumerState<UpdateScreen> createState() => _UpdateScreenState();
}

class _UpdateScreenState extends ConsumerState<UpdateScreen> {
  double? _progress;
  String? _message;

  Future<void> _install() async {
    final release = ref.read(updateProvider).value;
    if (release == null) return;
    setState(() => _progress = 0);
    try {
      final file = await downloadUpdate(ref.read(apiClientProvider), release,
          onProgress: (p) => setState(() => _progress = p));
      if (Platform.isWindows) {
        await Process.start(file.path, ['/SILENT', '/CLOSEAPPLICATIONS'], mode: ProcessStartMode.detached);
        exit(0);
      }
      final appImage = Platform.environment['APPIMAGE'];
      if (Platform.isLinux && appImage != null && file.path.endsWith('.AppImage')) {
        await file.copy(appImage);
        await Process.run('chmod', ['+x', appImage]);
        setState(() => _message = 'Перезапустите приложение.');
        return;
      }
      setState(() => _message = file.path.endsWith('.deb')
          ? 'sudo apt install ${file.path}'
          : (file.path.endsWith('.rpm') ? 'sudo dnf install ${file.path}' : file.path));
    } catch (e) {
      if (mounted) showError(context, e);
    } finally {
      if (mounted) setState(() => _progress = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final release = ref.watch(updateProvider).value;
    return Scaffold(
      appBar: AppBar(title: Text(release == null ? s.about : s.updateAvailable(release.version))),
      body: Readable(
        child: Padding(
          padding: const EdgeInsets.all(Gaps.l),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            if (release?.notes != null) Text(release!.notes!),
            const SizedBox(height: Gaps.l),
            if (_progress != null) LinearProgressIndicator(value: _progress),
            if (_message != null) SelectableText(_message!),
            const SizedBox(height: Gaps.l),
            FilledButton(onPressed: release == null || _progress != null ? null : _install,
                child: Text(s.updateInstall)),
          ]),
        ),
      ),
    );
  }
}
