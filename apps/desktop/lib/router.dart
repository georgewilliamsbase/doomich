import 'dart:convert';
import 'dart:io';

import 'package:doomich_core/doomich_core.dart';
import 'package:doomich_ui/doomich_ui.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'hotkeys.dart';
import 'update.dart';

final desktopRouterProvider = Provider<GoRouter>((ref) {
  final refresh = ValueNotifier<int>(0);
  ref.listen(authProvider, (_, _) => refresh.value++);
  ref.listen(settingsProvider.select((s) => s.acceptedTermsVersion), (_, _) => refresh.value++);
  ref.onDispose(refresh.dispose);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: refresh,
    redirect: (context, state) => _redirect(ref, state),
    routes: [
      GoRoute(path: '/splash', builder: (_, _) => const Scaffold(body: Center(child: Mascot(size: 120)))),
      GoRoute(path: Routes.welcome, builder: (_, _) => const WelcomeScreen()),
      GoRoute(path: Routes.invite, builder: (_, s) => InviteScreen(initialCode: s.uri.queryParameters['code'])),
      GoRoute(path: Routes.register, builder: (_, _) => const RegisterScreen()),
      GoRoute(path: Routes.recoveryCode, builder: (_, _) => const RecoveryCodeScreen(onSaveFile: _saveRecovery)),
      GoRoute(path: Routes.terms, builder: (_, _) => const TermsScreen()),
      GoRoute(
        path: Routes.group,
        builder: (_, s) => GroupScreen(popOnDone: s.uri.queryParameters['from'] == 'settings'),
      ),
      GoRoute(path: Routes.login, builder: (_, _) => const LoginScreen(showQr: true)),
      GoRoute(path: Routes.recover, builder: (_, _) => const RecoverScreen()),
      GoRoute(
        path: Routes.qrLogin,
        builder: (context, _) => QrLoginScreen(onSignedIn: () => context.go(Routes.chats)),
      ),
      GoRoute(
        path: '/documents/:doc/chunks/:chunk',
        builder: (_, s) => SourceScreen(documentId: s.pathParameters['doc']!, chunkId: s.pathParameters['chunk']!),
      ),
      GoRoute(path: Routes.sessions, builder: (_, _) => const SessionsScreen()),
      GoRoute(path: Routes.legal, builder: (_, s) => LegalScreen(doc: s.uri.queryParameters['doc'])),
      GoRoute(path: '/update', builder: (_, _) => const UpdateScreen()),
      ShellRoute(
        builder: (context, state, child) => DesktopShell(location: state.matchedLocation, child: child),
        routes: [
          GoRoute(path: Routes.chats, builder: (_, _) => const ChatsPane(chatId: null), routes: [
            GoRoute(path: ':id', builder: (_, s) => ChatsPane(chatId: s.pathParameters['id'])),
          ]),
          GoRoute(path: Routes.schedule, builder: (_, _) => const ScheduleView(showAppBar: false)),
          GoRoute(path: Routes.documents, builder: (context, _) => DocumentsView(showAppBar: false,
              onAsk: (id) => context.go(Routes.chat(id)))),
          GoRoute(path: Routes.settings, builder: (_, _) => const SettingsView(showAppBar: false)),
        ],
      ),
    ],
  );
});

String? _redirect(Ref ref, GoRouterState state) {
  final auth = ref.read(authProvider);
  final loc = state.matchedLocation;
  if (auth.isLoading && !auth.hasValue) return loc == '/splash' ? null : '/splash';
  final signedIn = auth.value is SignedIn;
  final onboarding = Routes.onboarding.contains(loc);
  if (!signedIn) return onboarding ? null : Routes.welcome;
  if (loc == Routes.recoveryCode) return null;
  final accepted = ref.read(settingsProvider).acceptedTermsVersion >= termsVersion;
  if (!accepted) return loc == Routes.terms || loc == Routes.legal ? null : Routes.terms;
  if (loc == Routes.group) return null;
  if (onboarding || loc == '/splash') return Routes.chats;
  return null;
}

Future<void> _saveRecovery(String text) async {
  await FilePicker.saveFile(fileName: 'doomich-recovery-code.txt', bytes: Uint8List.fromList(utf8.encode(text)),
      mimeType: 'text/plain');
}

class _NewChatIntent extends Intent {
  const _NewChatIntent();
}

class _SettingsIntent extends Intent {
  const _SettingsIntent();
}

class _VoiceIntent extends Intent {
  const _VoiceIntent();
}

/// Оболочка ПК: боковая навигация слева, содержимое справа, сочетания клавиш.
class DesktopShell extends ConsumerWidget {
  const DesktopShell({super.key, required this.location, required this.child});

  final String location;
  final Widget child;

  static const _tabs = [Routes.chats, Routes.schedule, Routes.documents, Routes.settings];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final index = _tabs.indexWhere((t) => location.startsWith(t)).clamp(0, _tabs.length - 1);
    final update = ref.watch(updateProvider).value;
    return Shortcuts(
      shortcuts: const {
        SingleActivator(LogicalKeyboardKey.keyN, control: true): _NewChatIntent(),
        SingleActivator(LogicalKeyboardKey.comma, control: true): _SettingsIntent(),
        SingleActivator(LogicalKeyboardKey.keyM, control: true): _VoiceIntent(),
      },
      child: Actions(
        actions: {
          _NewChatIntent: CallbackAction<_NewChatIntent>(onInvoke: (_) async {
            final chat = await ref.read(chatListProvider.notifier).create();
            if (context.mounted) context.go(Routes.chat(chat.id));
            return null;
          }),
          _SettingsIntent: CallbackAction<_SettingsIntent>(onInvoke: (_) {
            context.go(Routes.settings);
            return null;
          }),
          _VoiceIntent: CallbackAction<_VoiceIntent>(onInvoke: (_) {
            final voice = ref.read(voiceProvider.notifier);
            ref.read(voiceProvider).phase == VoicePhase.listening ? voice.send() : voice.listen();
            return null;
          }),
        },
        child: Focus(
          autofocus: true,
          child: Scaffold(
            body: Row(children: [
              NavigationRail(
                selectedIndex: index,
                labelType: NavigationRailLabelType.all,
                leading: const Padding(padding: EdgeInsets.symmetric(vertical: Gaps.m), child: Mascot(size: 40)),
                trailing: update == null
                    ? null
                    : Padding(
                        padding: const EdgeInsets.only(top: Gaps.l),
                        child: IconButton(icon: const Icon(Icons.system_update), tooltip: s.updateAvailable(update.version),
                            onPressed: () => context.push('/update')),
                      ),
                onDestinationSelected: (i) => context.go(_tabs[i]),
                destinations: [
                  NavigationRailDestination(icon: const Icon(Icons.forum_outlined), selectedIcon: const Icon(Icons.forum),
                      label: Text(s.tabChat)),
                  NavigationRailDestination(icon: const Icon(Icons.event_note_outlined),
                      selectedIcon: const Icon(Icons.event_note), label: Text(s.tabSchedule)),
                  NavigationRailDestination(icon: const Icon(Icons.description_outlined),
                      selectedIcon: const Icon(Icons.description), label: Text(s.tabDocuments)),
                  NavigationRailDestination(icon: const Icon(Icons.settings_outlined),
                      selectedIcon: const Icon(Icons.settings), label: Text(s.tabSettings)),
                ],
              ),
              const VerticalDivider(width: 1),
              Expanded(child: child),
            ]),
          ),
        ),
      ),
    );
  }
}

/// Чаты на ПК: список слева, открытый чат справа.
class ChatsPane extends ConsumerWidget {
  const ChatsPane({super.key, required this.chatId});

  final String? chatId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    GlobalHotkeys.setActive(chatId == incognitoChat ? null : chatId);
    return Row(children: [
      SizedBox(
        width: 320,
        child: Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(Gaps.m, Gaps.m, Gaps.m, 0),
            child: Row(children: [
              Text(s.chats, style: Theme.of(context).textTheme.titleLarge),
            ]),
          ),
          Expanded(child: ChatListView(dense: true, selectedId: chatId, onOpen: (id) => context.go(Routes.chat(id)))),
          Padding(
            padding: const EdgeInsets.all(Gaps.s),
            child: Text(s.hotkeyHint, style: Theme.of(context).textTheme.bodySmall, textAlign: TextAlign.center),
          ),
        ]),
      ),
      const VerticalDivider(width: 1),
      Expanded(
        child: chatId == null
            ? EmptyState(text: s.chatEmpty, mood: MascotMood.happy)
            : ChatView(key: ValueKey(chatId), chatId: chatId!),
      ),
    ]);
  }
}

bool get isWindows => Platform.isWindows;
