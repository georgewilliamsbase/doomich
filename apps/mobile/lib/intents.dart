import 'dart:async';

import 'package:app_links/app_links.dart';
import 'package:doomich_ui/doomich_ui.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:receive_sharing_intent/receive_sharing_intent.dart';

/// Файлы, пришедшие через "Поделиться" из других приложений.
class SharedFiles extends Notifier<List<String>> {
  @override
  List<String> build() => const [];

  void set(List<String> files) => state = files;

  List<String> take() {
    final f = state;
    state = const [];
    return f;
  }
}

final sharedFilesProvider = NotifierProvider<SharedFiles, List<String>>(SharedFiles.new);

/// Ссылки doomich://invite/... и doomich://qr-login, а также "Поделиться" файлом.
class IntentListener extends ConsumerStatefulWidget {
  const IntentListener({super.key, required this.router, required this.child});

  final GoRouter router;
  final Widget child;

  @override
  ConsumerState<IntentListener> createState() => _IntentListenerState();
}

class _IntentListenerState extends ConsumerState<IntentListener> {
  final _links = AppLinks();
  StreamSubscription<Uri>? _linkSub;
  StreamSubscription<List<SharedMediaFile>>? _shareSub;

  @override
  void initState() {
    super.initState();
    _linkSub = _links.uriLinkStream.listen(_onLink);
    _shareSub = ReceiveSharingIntent.instance.getMediaStream().listen(_onShared);
    ReceiveSharingIntent.instance.getInitialMedia().then((files) {
      _onShared(files);
      ReceiveSharingIntent.instance.reset();
    });
  }

  void _onLink(Uri uri) {
    if (uri.scheme != 'doomich') return;
    if (uri.host == 'invite') {
      widget.router.go('${Routes.invite}?code=${Uri.encodeComponent(uri.toString())}');
    } else if (uri.host == 'qr-login') {
      widget.router.go('${Routes.settings}?qr=${uri.queryParameters['t'] ?? ''}');
    }
  }

  void _onShared(List<SharedMediaFile> files) {
    final paths = files.map((f) => f.path).where((p) => p.isNotEmpty).toList();
    if (paths.isEmpty) return;
    ref.read(sharedFilesProvider.notifier).set(paths);
    widget.router.go(Routes.documents);
  }

  @override
  void dispose() {
    _linkSub?.cancel();
    _shareSub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
