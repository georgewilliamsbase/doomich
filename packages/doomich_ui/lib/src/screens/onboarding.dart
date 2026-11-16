import 'dart:async';

import 'package:doomich_api/doomich_api.dart';
import 'package:doomich_core/doomich_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../routes.dart';
import '../strings.dart';
import '../theme.dart';
import '../widgets/common.dart';
import '../widgets/mascot.dart';

/// Данные, которые переходят между шагами регистрации.
class OnboardingData {
  const OnboardingData({this.code, this.invite, this.recoveryCode});
  final String? code;
  final InviteCheckOut? invite;
  final String? recoveryCode;
}

class OnboardingNotifier extends Notifier<OnboardingData> {
  @override
  OnboardingData build() => const OnboardingData();

  void setInvite(String code, InviteCheckOut invite) => state = OnboardingData(code: code, invite: invite);

  void setRecovery(String code) => state = OnboardingData(code: state.code, invite: state.invite, recoveryCode: code);

  void clear() => state = const OnboardingData();
}

final onboardingProvider = NotifierProvider<OnboardingNotifier, OnboardingData>(OnboardingNotifier.new);

/// Версия пользовательского соглашения. При изменении текста увеличиваем, экран принятия покажется снова.
const termsVersion = 1;

class _Step extends StatelessWidget {
  const _Step({required this.title, required this.children, this.leading = true});

  final String title;
  final List<Widget> children;
  final bool leading;

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text(title), automaticallyImplyLeading: leading),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(Gaps.l),
            child: Readable(
              maxWidth: 480,
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: children),
            ),
          ),
        ),
      );
}

class WelcomeScreen extends ConsumerWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final settings = ref.watch(settingsProvider);
    final ctl = ref.read(settingsProvider.notifier);
    final text = Theme.of(context).textTheme;
    Widget feature(IconData icon, String t) => ListTile(leading: Icon(icon), title: Text(t), dense: true);
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(Gaps.l),
          child: Readable(
            maxWidth: 480,
            child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              const SizedBox(height: Gaps.l),
              const Center(child: Mascot(size: 120, mood: MascotMood.happy)),
              const SizedBox(height: Gaps.m),
              Text(s.welcomeTitle, style: text.headlineMedium, textAlign: TextAlign.center),
              const SizedBox(height: Gaps.s),
              Text(s.welcomeBody, style: text.bodyLarge, textAlign: TextAlign.center),
              const SizedBox(height: Gaps.m),
              feature(Icons.forum_outlined, s.featureChat),
              feature(Icons.event_note_outlined, s.featureSchedule),
              feature(Icons.description_outlined, s.featureDocs),
              feature(Icons.shield_outlined, s.featurePrivacy),
              const SizedBox(height: Gaps.m),
              Row(children: [
                Expanded(
                  child: DropdownButtonFormField<String?>(
                    initialValue: settings.localeCode,
                    decoration: InputDecoration(labelText: s.language),
                    items: [
                      DropdownMenuItem(value: null, child: Text(s.languageSystem)),
                      const DropdownMenuItem(value: 'ru', child: Text('Русский')),
                      const DropdownMenuItem(value: 'en', child: Text('English')),
                    ],
                    onChanged: ctl.setLocale,
                  ),
                ),
                const SizedBox(width: Gaps.m),
                Expanded(
                  child: DropdownButtonFormField<ThemeMode>(
                    initialValue: settings.themeMode,
                    decoration: InputDecoration(labelText: s.theme),
                    items: [
                      DropdownMenuItem(value: ThemeMode.system, child: Text(s.themeSystem)),
                      DropdownMenuItem(value: ThemeMode.light, child: Text(s.themeLight)),
                      DropdownMenuItem(value: ThemeMode.dark, child: Text(s.themeDark)),
                    ],
                    onChanged: (m) => ctl.setThemeMode(m ?? ThemeMode.system),
                  ),
                ),
              ]),
              const SizedBox(height: Gaps.l),
              FilledButton(onPressed: () => context.push(Routes.invite), child: Text(s.start)),
              const SizedBox(height: Gaps.s),
              TextButton(onPressed: () => context.push(Routes.login), child: Text(s.haveAccount)),
            ]),
          ),
        ),
      ),
    );
  }
}

class InviteScreen extends ConsumerStatefulWidget {
  const InviteScreen({super.key, this.initialCode, this.onScan});

  final String? initialCode;

  /// Сканер QR есть только в мобильном приложении. Возвращает распознанный текст.
  final Future<String?> Function(BuildContext context)? onScan;

  @override
  ConsumerState<InviteScreen> createState() => _InviteScreenState();
}

class _InviteScreenState extends ConsumerState<InviteScreen> {
  late final _code = TextEditingController(text: widget.initialCode);
  bool _busy = false;
  InviteCheckOut? _found;

  @override
  void initState() {
    super.initState();
    if (widget.initialCode != null) Future.microtask(_check);
  }

  Future<void> _check() async {
    final raw = _code.text.trim();
    if (raw.isEmpty) return;
    setState(() => _busy = true);
    try {
      final info = await ref.read(authProvider.notifier).checkInvite(raw);
      final code = InviteLink.parse(raw)?.code ?? raw;
      ref.read(onboardingProvider.notifier).setInvite(code, info);
      setState(() => _found = info);
    } catch (e) {
      if (mounted) showError(context, e);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return _Step(title: s.inviteTitle, children: [
      Text(s.inviteHint),
      const SizedBox(height: Gaps.m),
      TextField(
        controller: _code,
        autofocus: widget.initialCode == null,
        textCapitalization: TextCapitalization.characters,
        decoration: InputDecoration(labelText: s.inviteField, hintText: 'ABCD-EFGH'),
        inputFormatters: [LengthLimitingTextInputFormatter(200)],
        onSubmitted: (_) => _check(),
      ),
      if (widget.onScan != null) ...[
        const SizedBox(height: Gaps.s),
        OutlinedButton.icon(
          icon: const Icon(Icons.qr_code_scanner),
          label: Text(s.inviteScan),
          onPressed: () async {
            final text = await widget.onScan!(context);
            if (text != null) {
              _code.text = text;
              await _check();
            }
          },
        ),
      ],
      const SizedBox(height: Gaps.m),
      if (_found != null)
        Card(
          child: ListTile(
            leading: const Icon(Icons.verified_outlined),
            title: Text(s.inviteFor(_found!.tenant.shortName ?? _found!.tenant.name)),
            subtitle: Text([roleText(s, _found!.role), if (_found!.group != null) _found!.group!.code].join(' · ')),
          ),
        ),
      const SizedBox(height: Gaps.m),
      FilledButton(
        onPressed: _busy ? null : (_found == null ? _check : () => context.push(Routes.register)),
        child: _busy ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2))
            : Text(s.next),
      ),
      TextButton(
        onPressed: () => showDialog<void>(
          context: context,
          builder: (ctx) => AlertDialog(title: Text(s.inviteNoCode), content: Text(s.inviteNoCodeBody),
              actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: Text(s.ok))]),
        ),
        child: Text(s.inviteNoCode),
      ),
    ]);
  }
}

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _gen = PseudonymGenerator();
  final _login = TextEditingController();
  final _password = TextEditingController();
  final _repeat = TextEditingController();
  bool _busy = false;
  bool _obscure = true;
  bool? _available;
  Timer? _debounce;
  List<String> _suggestions = const [];

  @override
  void initState() {
    super.initState();
    _suggestions = _gen.suggestions(count: 3);
    _login.text = _suggestions.first;
    _scheduleCheck();
  }

  void _scheduleCheck() {
    _debounce?.cancel();
    setState(() => _available = null);
    _debounce = Timer(const Duration(milliseconds: 500), () async {
      final value = _login.text.trim();
      if (!LoginRules.isValid(value)) return;
      try {
        final r = await ref.read(apiClientProvider).checkLogin(value);
        if (mounted && _login.text.trim() == value) setState(() => _available = r.available);
      } catch (_) {}
    });
  }

  String? _strengthLabel(S s, int score) => switch (score) {
        0 || 1 => s.passwordWeak,
        2 => s.passwordFair,
        3 => s.passwordGood,
        _ => s.passwordStrong,
      };

  Future<void> _submit() async {
    final data = ref.read(onboardingProvider);
    final s = context.s;
    if (_password.text != _repeat.text) {
      showInfo(context, s.passwordMismatch);
      return;
    }
    setState(() => _busy = true);
    try {
      final locale = ref.read(settingsProvider).localeCode ?? Localizations.localeOf(context).languageCode;
      final out = await ref.read(authProvider.notifier).register(
            inviteCode: data.code ?? '', login: _login.text.trim(), password: _password.text,
            locale: locale == 'en' ? 'en' : 'ru');
      ref.read(onboardingProvider.notifier).setRecovery(out.recoveryCode);
      if (mounted) context.go(Routes.recoveryCode);
    } catch (e) {
      if (mounted) showError(context, e);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final login = _login.text.trim();
    final valid = LoginRules.isValid(login);
    final warning = LoginRules.warning(login);
    final score = passwordScore(_password.text, login: login);
    final canSubmit = valid && _available != false && _password.text.length >= 10 && score >= 2 && !_busy;
    return _Step(title: s.registerTitle, children: [
      TextField(
        controller: _login,
        decoration: InputDecoration(
          labelText: s.nickname,
          helperText: s.nicknameHint,
          errorText: login.isEmpty || valid ? (_available == false ? s.nicknameTaken : null) : s.nicknameInvalid,
          suffixIcon: _available == true ? const Icon(Icons.check_circle_outline) : null,
        ),
        onChanged: (_) => _scheduleCheck(),
      ),
      if (warning != null)
        Padding(
          padding: const EdgeInsets.only(top: Gaps.xs),
          child: Text(s.nicknameLooksLikeName, style: TextStyle(color: Theme.of(context).colorScheme.tertiary)),
        ),
      Wrap(spacing: Gaps.s, children: [
        for (final p in _suggestions)
          ActionChip(label: Text(p), onPressed: () {
            _login.text = p;
            _scheduleCheck();
          }),
        ActionChip(
          avatar: const Icon(Icons.casino_outlined, size: 18),
          label: Text(s.nicknameSuggest),
          onPressed: () => setState(() => _suggestions = _gen.suggestions(count: 3)),
        ),
      ]),
      const SizedBox(height: Gaps.m),
      TextField(
        controller: _password,
        obscureText: _obscure,
        decoration: InputDecoration(
          labelText: s.password,
          helperText: _password.text.isEmpty ? s.passwordHint : _strengthLabel(s, score),
          suffixIcon: IconButton(icon: Icon(_obscure ? Icons.visibility : Icons.visibility_off),
              onPressed: () => setState(() => _obscure = !_obscure)),
        ),
        onChanged: (_) => setState(() {}),
      ),
      if (_password.text.isNotEmpty)
        Padding(
          padding: const EdgeInsets.only(top: Gaps.xs),
          child: LinearProgressIndicator(value: (score + 1) / 5),
        ),
      const SizedBox(height: Gaps.m),
      TextField(
        controller: _repeat,
        obscureText: _obscure,
        decoration: InputDecoration(labelText: s.passwordRepeat),
        onChanged: (_) => setState(() {}),
        onSubmitted: (_) => canSubmit ? _submit() : null,
      ),
      const SizedBox(height: Gaps.l),
      FilledButton(onPressed: canSubmit ? _submit : null, child: Text(s.createAccount)),
    ]);
  }
}

class RecoveryCodeScreen extends ConsumerStatefulWidget {
  const RecoveryCodeScreen({super.key, this.onShare, this.onSaveFile, this.next = Routes.terms});

  /// Мобильное приложение передаёт "Поделиться", ПК: сохранение в файл
  final Future<void> Function(String text)? onShare;
  final Future<void> Function(String text)? onSaveFile;
  final String next;

  @override
  ConsumerState<RecoveryCodeScreen> createState() => _RecoveryCodeScreenState();
}

class _RecoveryCodeScreenState extends ConsumerState<RecoveryCodeScreen> {
  bool _saved = false;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final code = ref.watch(onboardingProvider).recoveryCode ?? '';
    final login = ref.watch(meProvider)?.login ?? '';
    final fileText = '${s.appName}\n${s.nickname}: $login\n${s.recoveryCode}: $code\n';
    return _Step(title: s.recoveryTitle, leading: false, children: [
      Text(s.recoveryBody),
      const SizedBox(height: Gaps.l),
      Card(
        child: Padding(
          padding: const EdgeInsets.all(Gaps.m),
          child: SelectableText(code, textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontFamily: 'monospace', letterSpacing: 1.5)),
        ),
      ),
      const SizedBox(height: Gaps.m),
      Wrap(spacing: Gaps.s, runSpacing: Gaps.s, alignment: WrapAlignment.center, children: [
        OutlinedButton.icon(
          icon: const Icon(Icons.copy),
          label: Text(s.copy),
          onPressed: () async {
            await Clipboard.setData(ClipboardData(text: code));
            if (context.mounted) showInfo(context, s.copied);
          },
        ),
        if (widget.onSaveFile != null)
          OutlinedButton.icon(icon: const Icon(Icons.save_alt), label: Text(s.recoverySaveFile),
              onPressed: () => widget.onSaveFile!(fileText)),
        if (widget.onShare != null)
          OutlinedButton.icon(icon: const Icon(Icons.share), label: Text(s.recoveryShare),
              onPressed: () => widget.onShare!(fileText)),
      ]),
      const SizedBox(height: Gaps.m),
      CheckboxListTile(value: _saved, onChanged: (v) => setState(() => _saved = v ?? false),
          title: Text(s.recoveryConfirm)),
      const SizedBox(height: Gaps.m),
      FilledButton(onPressed: _saved ? () => context.go(widget.next) : null, child: Text(s.next)),
    ]);
  }
}

class TermsScreen extends ConsumerStatefulWidget {
  const TermsScreen({super.key});

  @override
  ConsumerState<TermsScreen> createState() => _TermsScreenState();
}

class _TermsScreenState extends ConsumerState<TermsScreen> {
  bool _accepted = false;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return _Step(title: s.termsTitle, leading: false, children: [
      ListTile(leading: const Icon(Icons.gavel_outlined), title: Text(s.termsOpen),
          trailing: const Icon(Icons.chevron_right), onTap: () => context.push('${Routes.legal}?doc=terms')),
      ListTile(leading: const Icon(Icons.privacy_tip_outlined), title: Text(s.dataOpen),
          trailing: const Icon(Icons.chevron_right), onTap: () => context.push('${Routes.legal}?doc=data')),
      const SizedBox(height: Gaps.s),
      Text(s.aiNotice, style: Theme.of(context).textTheme.bodySmall),
      CheckboxListTile(value: _accepted, onChanged: (v) => setState(() => _accepted = v ?? false),
          title: Text(s.termsAccept)),
      const SizedBox(height: Gaps.m),
      FilledButton(
        onPressed: !_accepted
            ? null
            : () async {
                await ref.read(settingsProvider.notifier)
                    .update((x) => x.copyWith(acceptedTermsVersion: termsVersion, onboardingDone: true));
                if (!context.mounted) return;
                final me = ref.read(meProvider);
                context.go(me?.group == null ? Routes.group : Routes.chats);
              },
        child: Text(s.next),
      ),
    ]);
  }
}

/// Выбор группы: на сервере или только на устройстве.
class GroupScreen extends ConsumerStatefulWidget {
  const GroupScreen({super.key, this.popOnDone = false});

  /// true, если экран открыт из настроек, а не из онбординга
  final bool popOnDone;

  @override
  ConsumerState<GroupScreen> createState() => _GroupScreenState();
}

class _GroupScreenState extends ConsumerState<GroupScreen> {
  String _query = '';
  GroupOut? _selected;
  String? _subgroup;
  bool _onServer = true;
  bool _busy = false;

  void _finish() {
    if (widget.popOnDone) {
      context.pop();
    } else {
      context.go(Routes.chats);
    }
  }

  Future<void> _save() async {
    final g = _selected;
    if (g == null) return;
    setState(() => _busy = true);
    try {
      final settings = ref.read(settingsProvider.notifier);
      if (_onServer) {
        await ref.read(authProvider.notifier).updateMe(MePatch(groupId: g.id, subgroup: _subgroup));
        await settings.update((s) => s.copyWith(deviceGroupId: null, deviceGroupCode: null, deviceSubgroup: null));
      } else {
        await ref.read(authProvider.notifier).updateMe(const MePatch(clearGroup: true));
        await settings.update((s) => s.copyWith(deviceGroupId: g.id, deviceGroupCode: g.code, deviceSubgroup: _subgroup));
      }
      if (mounted) _finish();
    } catch (e) {
      if (mounted) showError(context, e);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final groups = ref.watch(groupSearchProvider(_query));
    return Scaffold(
      appBar: AppBar(title: Text(s.groupTitle), automaticallyImplyLeading: widget.popOnDone),
      body: Readable(
        maxWidth: 560,
        child: Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(Gaps.m, Gaps.m, Gaps.m, 0),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(s.groupBody),
              const SizedBox(height: Gaps.m),
              TextField(
                decoration: InputDecoration(labelText: s.groupSearch, prefixIcon: const Icon(Icons.search)),
                onChanged: (v) => setState(() => _query = v.trim()),
              ),
            ]),
          ),
          Expanded(
            child: groups.when(
              loading: () => const LoadingView(),
              error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(groupSearchProvider(_query))),
              data: (items) => ListView(children: [
                for (final g in items)
                  ListTile(
                    title: Text(g.code),
                    subtitle: Text([if (g.name != null) g.name!, if (g.faculty != null) g.faculty!].join(' · ')),
                    leading: Icon(_selected?.id == g.id ? Icons.radio_button_checked : Icons.radio_button_unchecked),
                    onTap: () => setState(() {
                      _selected = g;
                      _subgroup = null;
                    }),
                  ),
              ]),
            ),
          ),
          if (_selected != null)
            Padding(
              padding: const EdgeInsets.all(Gaps.m),
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                if (_selected!.subgroups.isNotEmpty)
                  DropdownButtonFormField<String?>(
                    initialValue: _subgroup,
                    decoration: InputDecoration(labelText: s.subgroup),
                    items: [
                      DropdownMenuItem(value: null, child: Text(s.subgroupAny)),
                      for (final sg in _selected!.subgroups) DropdownMenuItem(value: sg, child: Text(sg)),
                    ],
                    onChanged: (v) => setState(() => _subgroup = v),
                  ),
                SegmentedButton<bool>(
                  segments: [
                    ButtonSegment(value: true, label: Text(s.groupOnServer), icon: const Icon(Icons.cloud_outlined)),
                    ButtonSegment(value: false, label: Text(s.groupOnDevice),
                        icon: const Icon(Icons.phone_android_outlined)),
                  ],
                  selected: {_onServer},
                  onSelectionChanged: (v) => setState(() => _onServer = v.first),
                ),
                const SizedBox(height: Gaps.s),
                FilledButton(onPressed: _busy ? null : _save, child: Text(s.save)),
              ]),
            ),
          if (_selected == null && !widget.popOnDone)
            Padding(
              padding: const EdgeInsets.all(Gaps.m),
              child: TextButton(onPressed: _finish, child: Text(s.groupLater)),
            ),
        ]),
      ),
    );
  }
}

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key, this.showQr = false});

  /// На ПК можно войти по QR с телефона
  final bool showQr;

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _login = TextEditingController();
  final _password = TextEditingController();
  bool _busy = false;

  Future<void> _submit() async {
    setState(() => _busy = true);
    try {
      await ref.read(authProvider.notifier).login(_login.text.trim(), _password.text);
      await ref.read(settingsProvider.notifier).update((s) => s.copyWith(onboardingDone: true));
      if (!mounted) return;
      final accepted = ref.read(settingsProvider).acceptedTermsVersion >= termsVersion;
      context.go(accepted ? Routes.chats : Routes.terms);
    } catch (e) {
      if (mounted) showError(context, e);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return _Step(title: s.loginTitle, children: [
      TextField(controller: _login, decoration: InputDecoration(labelText: s.nickname), autofocus: true,
          textInputAction: TextInputAction.next),
      const SizedBox(height: Gaps.m),
      TextField(controller: _password, obscureText: true, decoration: InputDecoration(labelText: s.password),
          onSubmitted: (_) => _submit()),
      const SizedBox(height: Gaps.l),
      FilledButton(onPressed: _busy ? null : _submit, child: Text(s.login)),
      TextButton(onPressed: () => context.push(Routes.recover), child: Text(s.forgotPassword)),
      if (widget.showQr) ...[
        const Divider(height: Gaps.xl),
        OutlinedButton.icon(icon: const Icon(Icons.qr_code_2), label: Text(s.qrLoginTitle),
            onPressed: () => context.push(Routes.qrLogin)),
      ],
    ]);
  }
}

class RecoverScreen extends ConsumerStatefulWidget {
  const RecoverScreen({super.key});

  @override
  ConsumerState<RecoverScreen> createState() => _RecoverScreenState();
}

class _RecoverScreenState extends ConsumerState<RecoverScreen> {
  final _login = TextEditingController();
  final _code = TextEditingController();
  final _password = TextEditingController();
  bool _busy = false;

  Future<void> _submit() async {
    setState(() => _busy = true);
    try {
      final newCode = await ref.read(authProvider.notifier)
          .recover(login: _login.text.trim(), code: _code.text.trim(), newPassword: _password.text);
      ref.read(onboardingProvider.notifier).setRecovery(newCode);
      if (mounted) context.go(Routes.recoveryCode);
    } catch (e) {
      if (mounted) showError(context, e);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return _Step(title: s.recoverTitle, children: [
      TextField(controller: _login, decoration: InputDecoration(labelText: s.nickname)),
      const SizedBox(height: Gaps.m),
      TextField(controller: _code, decoration: InputDecoration(labelText: s.recoveryCode, hintText: 'XXXXX-XXXXX-XXXXX-XXXXX'),
          textCapitalization: TextCapitalization.characters),
      const SizedBox(height: Gaps.m),
      TextField(controller: _password, obscureText: true,
          decoration: InputDecoration(labelText: s.newPassword, helperText: s.passwordHint)),
      const SizedBox(height: Gaps.l),
      FilledButton(onPressed: _busy ? null : _submit, child: Text(s.recover)),
    ]);
  }
}
