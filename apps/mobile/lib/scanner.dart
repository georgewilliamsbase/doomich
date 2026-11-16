import 'package:doomich_ui/doomich_ui.dart';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

/// Сканер QR: код приглашения или вход на ПК. Кадры камеры никуда не отправляются.
Future<String?> scanQr(BuildContext context) =>
    Navigator.of(context).push<String>(MaterialPageRoute(builder: (_) => const _ScannerPage()));

class _ScannerPage extends StatefulWidget {
  const _ScannerPage();

  @override
  State<_ScannerPage> createState() => _ScannerPageState();
}

class _ScannerPageState extends State<_ScannerPage> {
  bool _done = false;

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text(context.s.inviteScan)),
        body: MobileScanner(
          onDetect: (capture) {
            if (_done) return;
            final value = capture.barcodes.map((b) => b.rawValue).whereType<String>().firstOrNull;
            if (value == null) return;
            _done = true;
            Navigator.of(context).pop(value);
          },
        ),
      );
}
