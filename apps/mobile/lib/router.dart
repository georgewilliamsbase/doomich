import 'package:doomich_core/doomich_core.dart';
import 'package:doomich_ui/doomich_ui.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:share_plus/share_plus.dart';

import 'intents.dart';
import 'scanner.dart';

/// Роутер мобильного приложения. Переходы между онбордингом и основным
/// интерфейсом решаются в redirect по состоянию входа.
final routerProvider = Provider<GoRouter>((ref) {
  final refresh = ValueNotifier<int>(0);
  ref.listen(authProvider, (_, _) => refresh.value++);
  ref.listen(settingsProvider.select((s) => s.acceptedTermsVersion), (_, _) => refresh.value++);
  ref.onDispose(refresh.dispose);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: refresh,
    redirect: (context, state) => _redirect(ref, state),
    routes: [
      GoRoute(path: '/splash', builder: (_, _) => const _Splash()),
      GoRoute(path: Routes.welcome, builder: (_, _) => const WelcomeScreen()),
      GoRoute(
        path: Routes.invite,
        builder: (_, s) => InviteScreen(initialCode: s.uri.queryParameters['code'], onScan: scanQr),
      ),
      GoRoute(path: Routes.register, builder: (_, _) => const RegisterScreen()),
      GoRoute(
        path: Routes.recoveryCode,
        builder: (_, _) => RecoveryCodeScreen(
          onShare: (text) => SharePlus.instance.share(ShareParams(text: text)),
        ),
      ),
      GoRoute(path: Routes.terms, builder: (_, _) => const TermsScreen()),
      GoRoute(
        path: Routes.group,
        builder: (_, s) => GroupScreen(popOnDone: s.uri.queryParameters['from'] == 'settings'),
      ),
      GoRoute(path: Routes.login, builder: (_, _) => const LoginScreen()),
      GoRoute(path: Routes.recover, builder: (_, _) => const RecoverScreen()),
      GoRoute(path: '/voice', builder: (_, s) => VoiceScreen(chatId: s.uri.queryParameters['chat'])),
      GoRoute(
        path: '/documents/:doc/chunks/:chunk',
        builder: (_, s) => SourceScreen(documentId: s.pathParameters['doc']!, chunkId: s.pathParameters['chunk']!),
      ),
      GoRoute(path: Routes.sessions, builder: (_, _) => const SessionsScreen()),
      GoRoute(path: Routes.legal, builder: (_, s) => LegalScreen(doc: s.uri.queryParameters['doc'])),
      StatefulShellRoute.indexedStack(
        builder: (context, state, shell) => _MobileShell(shell: shell),
        branches: [
          StatefulShellBranch(routes: [
            GoRoute(
              path: Routes.chats,
              builder: (context, _) => Scaffold(
                appBar: AppBar(title: Text(context.s.chats)),
                body: ChatListView(onOpen: (id) => context.push(Routes.chat(id))),
              ),
              routes: [
                GoRoute(path: ':id', builder: (_, s) => _ChatPage(chatId: s.pathParameters['id']!)),
              ],
            ),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(path: Routes.schedule, builder: (_, _) => const ScheduleView()),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(path: Routes.documents, builder: (_, _) => const _DocumentsPage()),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(path: Routes.settings, builder: (_, s) => _SettingsPage(qrToken: s.uri.queryParameters['qr'])),
          ]),
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
  if (!signedIn) {
    if (onboarding) return null;
    return Routes.welcome;
  }
  if (loc == Routes.recoveryCode) return null;
  final accepted = ref.read(settingsProvider).acceptedTermsVersion >= termsVersion;
  if (!accepted) return loc == Routes.terms || loc == Routes.legal ? null : Routes.terms;
  if (loc == Routes.group) return null;
  if (onboarding || loc == '/splash') return Routes.chats;
  return null;
}

class _Splash extends StatelessWidget {
  const _Splash();

  @override
  Widget build(BuildContext context) => const Scaffold(body: Center(child: Mascot(size: 120)));
}

class _MobileShell extends StatelessWidget {
  const _MobileShell({required this.shell});

  final StatefulNavigationShell shell;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return Scaffold(
      body: shell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: shell.currentIndex,
        onDestinationSelected: (i) => shell.goBranch(i, initialLocation: i == shell.currentIndex),
        destinations: [
          NavigationDestination(icon: const Icon(Icons.forum_outlined), selectedIcon: const Icon(Icons.forum),
              label: s.tabChat),
          NavigationDestination(icon: const Icon(Icons.event_note_outlined), selectedIcon: const Icon(Icons.event_note),
              label: s.tabSchedule),
          NavigationDestination(icon: const Icon(Icons.description_outlined), selectedIcon: const Icon(Icons.description),
              label: s.tabDocuments),
          NavigationDestination(icon: const Icon(Icons.settings_outlined), selectedIcon: const Icon(Icons.settings),
              label: s.tabSettings),
        ],
      ),
    );
  }
}

class _ChatPage extends StatelessWidget {
  const _ChatPage({required this.chatId});

  final String chatId;

  @override
  Widget build(BuildContext context) => ChatView(chatId: chatId);
}

class _DocumentsPage extends ConsumerWidget {
  const _DocumentsPage();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final files = ref.read(sharedFilesProvider.notifier).take();
    return DocumentsView(initialFiles: files, onAsk: (id) => context.push(Routes.chat(id)));
  }
}

class _SettingsPage extends ConsumerStatefulWidget {
  const _SettingsPage({this.qrToken});

  final String? qrToken;

  @override
  ConsumerState<_SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends ConsumerState<_SettingsPage> {
  @override
  void initState() {
    super.initState();
    final token = widget.qrToken;
    if (token != null && token.isNotEmpty) {
      // Пришли по ссылке doomich://qr-login: сразу спрашиваем подтверждение
      WidgetsBinding.instance.addPostFrameCallback((_) async {
        final s = context.s;
        if (await confirm(context, title: s.qrApproveTitle, body: s.qrApproveBody, action: s.qrApprove)) {
          try {
            await ref.read(apiClientProvider).qrApprove(token);
            if (mounted) showInfo(context, s.done);
          } catch (e) {
            if (mounted) showError(context, e);
          }
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) => SettingsView(onScanQrLogin: scanQr);
}
