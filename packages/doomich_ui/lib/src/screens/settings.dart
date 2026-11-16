import 'dart:async';

import 'package:doomich_api/doomich_api.dart';
import 'package:doomich_core/doomich_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../legal.dart';
import '../routes.dart';
import '../strings.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/mascot.dart';

class SettingsView extends ConsumerWidget {
  const SettingsView({super.key, this.showAppBar = true, this.onScanQrLogin, this.extra = const []});

  final bool showAppBar;

  /// Мобильное приложение передаёт сканер QR для входа на ПК
  final Future<String?> Function(BuildContext context)? onScanQrLogin;

  /// Дополнительные пункты платформы (например, выбор микрофона на ПК)
  final List<Widget> extra;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final settings = ref.watch(settingsProvider);
    final ctl = ref.read(settingsProvider.notifier);
    final me = ref.watch(meProvider);
    final config = ref.watch(appConfigProvider);
    final update = ref.watch(updateProvider).value;
    Widget header(String t) => Padding(
          padding: const EdgeInsets.fromLTRB(Gaps.m, Gaps.l, Gaps.m, Gaps.s),
          child: Text(t, style: Theme.of(context).textTheme.titleSmall?.copyWith(
              color: Theme.of(context).colorScheme.primary)),
        );

    final list = ListView(children: [
      if (me != null)
        ListTile(
          leading: const Mascot(size: 40),
          title: Text(me.login),
          subtitle: Text([roleText(s, me.role), me.tenant.shortName ?? me.tenant.name,
            if (me.group != null) me.group!.code].join(' · ')),
        ),
      if (update != null)
        Card(
          margin: const EdgeInsets.all(Gaps.m),
          child: ListTile(
            leading: const Icon(Icons.system_update),
            title: Text(s.updateAvailable(update.version)),
            subtitle: update.notes == null ? null : Text(update.notes!),
            trailing: FilledButton(onPressed: () => context.push('/update'), child: Text(s.updateInstall)),
          ),
        ),
      header(s.appearance),
      ListTile(
        leading: const Icon(Icons.palette_outlined),
        title: Text(s.theme),
        trailing: DropdownButton<ThemeMode>(
          value: settings.themeMode,
          onChanged: (m) => ctl.setThemeMode(m ?? ThemeMode.system),
          items: [
            DropdownMenuItem(value: ThemeMode.system, child: Text(s.themeSystem)),
            DropdownMenuItem(value: ThemeMode.light, child: Text(s.themeLight)),
            DropdownMenuItem(value: ThemeMode.dark, child: Text(s.themeDark)),
          ],
        ),
      ),
      ListTile(
        leading: const Icon(Icons.language),
        title: Text(s.language),
        trailing: DropdownButton<String?>(
          value: settings.localeCode,
          onChanged: (v) async {
            await ctl.setLocale(v);
            if (v != null) unawaited(ref.read(authProvider.notifier).updateMe(MePatch(locale: v)).catchError((_) => me!));
          },
          items: [
            DropdownMenuItem(value: null, child: Text(s.languageSystem)),
            const DropdownMenuItem(value: 'ru', child: Text('Русский')),
            const DropdownMenuItem(value: 'en', child: Text('English')),
          ],
        ),
      ),
      header(s.voice),
      SwitchListTile(
        secondary: const Icon(Icons.record_voice_over_outlined),
        title: Text(s.readAloud),
        value: settings.readAloud,
        onChanged: (v) => ctl.update((x) => x.copyWith(readAloud: v)),
      ),
      ListTile(
        leading: const Icon(Icons.speed),
        title: Text(s.speechRate),
        subtitle: Slider(
          value: settings.speechRate,
          min: 0.75,
          max: 1.5,
          divisions: 6,
          label: '${settings.speechRate.toStringAsFixed(2)}x',
          onChanged: (v) => ctl.update((x) => x.copyWith(speechRate: v)),
        ),
      ),
      ListTile(
        leading: const Icon(Icons.mic_none),
        title: Text(s.pttMode),
        trailing: DropdownButton<bool>(
          value: settings.holdToTalk,
          onChanged: (v) => ctl.update((x) => x.copyWith(holdToTalk: v ?? true)),
          items: [
            DropdownMenuItem(value: true, child: Text(s.pttHold)),
            DropdownMenuItem(value: false, child: Text(s.pttToggle)),
          ],
        ),
      ),
      ...extra,
      header(s.tabSchedule),
      ListTile(
        leading: const Icon(Icons.groups_outlined),
        title: Text(s.groupTitle),
        subtitle: Text(settings.deviceGroupCode != null
            ? '${settings.deviceGroupCode} (${s.groupOnDevice.toLowerCase()})'
            : (me?.group?.code ?? s.noGroup)),
        onTap: () => context.push('${Routes.group}?from=settings'),
      ),
      if (me?.role == 'teacher')
        ListTile(
          leading: const Icon(Icons.badge_outlined),
          title: Text(s.teacherMode),
          subtitle: Text(settings.teacherName ?? s.teacherNameHint),
          onTap: () => _teacherDialog(context, ref),
        ),
      header(s.privacy),
      ListTile(
        leading: const Icon(Icons.history),
        title: Text(s.historyRetention),
        trailing: DropdownButton<int>(
          value: me?.historyDays ?? 90,
          onChanged: (v) async {
            if (v == null) return;
            try {
              await ref.read(authProvider.notifier).updateMe(MePatch(historyDays: v));
            } catch (e) {
              if (context.mounted) showError(context, e);
            }
          },
          items: [
            for (final d in [7, 30, 90]) DropdownMenuItem(value: d, child: Text(s.days(d))),
            DropdownMenuItem(value: 0, child: Text(s.dontStore)),
          ],
        ),
      ),
      SwitchListTile(
        secondary: const Icon(Icons.visibility_off_outlined),
        title: Text(s.incognitoDefault),
        value: settings.incognitoByDefault,
        onChanged: (v) => ctl.update((x) => x.copyWith(incognitoByDefault: v)),
      ),
      header(s.account),
      if (onScanQrLogin != null)
        ListTile(
          leading: const Icon(Icons.qr_code_scanner),
          title: Text(s.signInOnPc),
          onTap: () => _approveQr(context, ref),
        ),
      ListTile(leading: const Icon(Icons.devices), title: Text(s.sessions), onTap: () => context.push(Routes.sessions)),
      ListTile(leading: const Icon(Icons.password), title: Text(s.changePassword),
          onTap: () => _changePassword(context, ref)),
      ListTile(leading: const Icon(Icons.logout), title: Text(s.logout), onTap: () async {
        await ref.read(authProvider.notifier).logout();
        if (context.mounted) context.go(Routes.welcome);
      }),
      ListTile(
        leading: Icon(Icons.delete_forever_outlined, color: Theme.of(context).colorScheme.error),
        title: Text(s.deleteAccount, style: TextStyle(color: Theme.of(context).colorScheme.error)),
        onTap: () => _deleteAccount(context, ref),
      ),
      header(s.about),
      ListTile(leading: const Icon(Icons.description_outlined), title: Text(s.legal),
          onTap: () => context.push(Routes.legal)),
      ListTile(leading: const Icon(Icons.bug_report_outlined), title: Text(s.reportProblem),
          onTap: () => _report(context, ref)),
      ListTile(leading: const Icon(Icons.info_outline), title: Text(s.version(config.version)),
          subtitle: Text(s.aiNotice)),
      const SizedBox(height: Gaps.xl),
    ]);
    if (!showAppBar) return list;
    return Scaffold(appBar: AppBar(title: Text(s.settings)), body: list);
  }

  Future<void> _teacherDialog(BuildContext context, WidgetRef ref) async {
    final s = context.s;
    final settings = ref.read(settingsProvider);
    final ctl = TextEditingController(text: settings.teacherName);
    final name = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.teacherMode),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: ctl, decoration: InputDecoration(labelText: s.teacherName)),
          const SizedBox(height: Gaps.s),
          Text(s.teacherNameHint, style: Theme.of(ctx).textTheme.bodySmall),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, ''), child: Text(s.delete)),
          FilledButton(onPressed: () => Navigator.pop(ctx, ctl.text.trim()), child: Text(s.save)),
        ],
      ),
    );
    if (name == null) return;
    final slug = ref.read(meProvider)?.tenant.slug ?? '';
    await ref.read(settingsProvider.notifier).update((x) => name.isEmpty
        ? x.copyWith(teacherName: null, teacherKey: null)
        : x.copyWith(teacherName: name, teacherKey: teacherKey(slug, name)));
  }

  Future<void> _approveQr(BuildContext context, WidgetRef ref) async {
    final s = context.s;
    final raw = await onScanQrLogin!(context);
    if (raw == null || !context.mounted) return;
    final token = Uri.tryParse(raw)?.queryParameters['t'] ?? raw;
    final ok = await confirm(context, title: s.qrApproveTitle, body: s.qrApproveBody, action: s.qrApprove);
    if (!ok) return;
    try {
      await ref.read(apiClientProvider).qrApprove(token);
      if (context.mounted) showInfo(context, s.done);
    } catch (e) {
      if (context.mounted) showError(context, e);
    }
  }

  Future<void> _changePassword(BuildContext context, WidgetRef ref) async {
    final s = context.s;
    final oldCtl = TextEditingController();
    final newCtl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.changePassword),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: oldCtl, obscureText: true, decoration: InputDecoration(labelText: s.oldPassword)),
          const SizedBox(height: Gaps.s),
          TextField(controller: newCtl, obscureText: true,
              decoration: InputDecoration(labelText: s.newPassword, helperText: s.passwordHint)),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(s.cancel)),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: Text(s.save)),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(apiClientProvider).changePassword(oldCtl.text, newCtl.text);
      if (context.mounted) showInfo(context, s.done);
    } catch (e) {
      if (context.mounted) showError(context, e);
    }
  }

  Future<void> _deleteAccount(BuildContext context, WidgetRef ref) async {
    final s = context.s;
    final pw = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.deleteAccount),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(s.deleteAccountBody),
          const SizedBox(height: Gaps.m),
          TextField(controller: pw, obscureText: true, decoration: InputDecoration(labelText: s.confirmPassword)),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(s.cancel)),
          FilledButton(style: FilledButton.styleFrom(backgroundColor: Theme.of(ctx).colorScheme.error),
              onPressed: () => Navigator.pop(ctx, true), child: Text(s.delete)),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(authProvider.notifier).deleteAccount(pw.text);
      if (context.mounted) context.go(Routes.welcome);
    } catch (e) {
      if (context.mounted) showError(context, e);
    }
  }

  Future<void> _report(BuildContext context, WidgetRef ref) async {
    final s = context.s;
    final ctl = TextEditingController();
    final text = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.reportProblem),
        content: TextField(controller: ctl, maxLines: 5, decoration: InputDecoration(labelText: s.feedbackComment)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: Text(s.cancel)),
          FilledButton(onPressed: () => Navigator.pop(ctx, ctl.text.trim()), child: Text(s.send)),
        ],
      ),
    );
    if (text == null || text.isEmpty) return;
    try {
      // Анонимно: без привязки к аккаунту, как и оценки ответов
      await ref.read(apiClientProvider).feedback(FeedbackIn(rating: -1, category: 'other', comment: text));
      if (context.mounted) showInfo(context, s.feedbackThanks);
    } catch (e) {
      if (context.mounted) showError(context, e);
    }
  }
}

class SessionsScreen extends ConsumerStatefulWidget {
  const SessionsScreen({super.key});

  @override
  ConsumerState<SessionsScreen> createState() => _SessionsScreenState();
}

class _SessionsScreenState extends ConsumerState<SessionsScreen> {
  late Future<List<SessionOut>> _future = ref.read(apiClientProvider).sessions();

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return Scaffold(
      appBar: AppBar(title: Text(s.sessions)),
      body: FutureBuilder<List<SessionOut>>(
        future: _future,
        builder: (context, snap) {
          if (snap.hasError) return ErrorView(error: snap.error!);
          if (!snap.hasData) return const LoadingView();
          return ListView(children: [
            for (final x in snap.data!)
              ListTile(
                leading: Icon(switch (x.platform) {
                  'android' || 'ios' => Icons.phone_android,
                  _ => Icons.computer,
                }),
                title: Text(x.platform ?? '-'),
                subtitle: Text(x.current ? s.thisDevice : '${x.createdOn.day}.${x.createdOn.month}.${x.createdOn.year}'),
                trailing: x.current
                    ? null
                    : IconButton(icon: const Icon(Icons.logout), tooltip: s.logout, onPressed: () async {
                        await ref.read(apiClientProvider).endSession(x.id);
                        setState(() => _future = ref.read(apiClientProvider).sessions());
                      }),
              ),
          ]);
        },
      ),
    );
  }
}

/// Вход на ПК по QR: ПК показывает код, телефон его сканирует и подтверждает.
class QrLoginScreen extends ConsumerStatefulWidget {
  const QrLoginScreen({super.key, required this.onSignedIn});

  final VoidCallback onSignedIn;

  @override
  ConsumerState<QrLoginScreen> createState() => _QrLoginScreenState();
}

class _QrLoginScreenState extends ConsumerState<QrLoginScreen> {
  String? _token;
  Timer? _timer;
  Object? _error;

  @override
  void initState() {
    super.initState();
    _start();
  }

  Future<void> _start() async {
    _timer?.cancel();
    try {
      final r = await ref.read(apiClientProvider).qrStart();
      setState(() {
        _token = r.token;
        _error = null;
      });
      _timer = Timer.periodic(const Duration(seconds: 2), (_) => _poll());
    } catch (e) {
      setState(() => _error = e);
    }
  }

  Future<void> _poll() async {
    final token = _token;
    if (token == null) return;
    try {
      final out = await ref.read(apiClientProvider).qrPoll(token);
      if (out != null) {
        _timer?.cancel();
        await ref.read(authProvider.notifier).signedInWith(out);
        widget.onSignedIn();
      }
    } on ApiException catch (e) {
      if (e.code == 'qr_expired') await _start();
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return Scaffold(
      appBar: AppBar(title: Text(s.qrLoginTitle)),
      body: Center(
        child: _error != null
            ? ErrorView(error: _error!, onRetry: _start)
            : _token == null
                ? const LoadingView()
                : Column(mainAxisSize: MainAxisSize.min, children: [
                    Container(
                      color: Colors.white,
                      padding: const EdgeInsets.all(Gaps.m),
                      child: QrImageView(data: 'doomich://qr-login?t=$_token', size: 240),
                    ),
                    const SizedBox(height: Gaps.l),
                    SizedBox(width: 360, child: Text(s.qrLoginBody, textAlign: TextAlign.center)),
                  ]),
      ),
    );
  }
}

class LegalScreen extends StatelessWidget {
  const LegalScreen({super.key, this.doc});

  final String? doc;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final en = Localizations.localeOf(context).languageCode == 'en';
    final docs = {'terms': (s.termsOpen, en ? termsEn : termsRu), 'data': (s.dataOpen, en ? dataEn : dataRu)};
    final selected = doc == null ? null : docs[doc];
    if (selected == null) {
      return Scaffold(
        appBar: AppBar(title: Text(s.legal)),
        body: ListView(children: [
          for (final e in docs.entries)
            ListTile(title: Text(e.value.$1), trailing: const Icon(Icons.chevron_right),
                onTap: () => context.push('${Routes.legal}?doc=${e.key}')),
        ]),
      );
    }
    return Scaffold(
      appBar: AppBar(title: Text(selected.$1)),
      body: Readable(child: SingleChildScrollView(padding: const EdgeInsets.all(Gaps.m), child: SelectableText(selected.$2))),
    );
  }
}
