import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Маскот Думыч: сова. Нарисована кодом, чтобы не держать картинки для каждой темы.
class Mascot extends StatelessWidget {
  const Mascot({super.key, this.size = 96, this.mood = MascotMood.calm});

  final double size;
  final MascotMood mood;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Semantics(
      label: 'Думыч',
      image: true,
      child: CustomPaint(size: Size.square(size), painter: _OwlPainter(scheme, mood)),
    );
  }
}

enum MascotMood { calm, listening, thinking, happy }

class _OwlPainter extends CustomPainter {
  _OwlPainter(this.scheme, this.mood);

  final ColorScheme scheme;
  final MascotMood mood;

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final body = Paint()..color = scheme.primary;
    final belly = Paint()..color = scheme.primaryContainer;
    final white = Paint()..color = Colors.white;
    final dark = Paint()..color = const Color(0xFF1B1B2F);
    final beak = Paint()..color = const Color(0xFFF2A541);

    // Уши-пёрышки
    final ears = Path()
      ..moveTo(w * 0.22, w * 0.28)
      ..lineTo(w * 0.18, w * 0.06)
      ..lineTo(w * 0.40, w * 0.20)
      ..moveTo(w * 0.78, w * 0.28)
      ..lineTo(w * 0.82, w * 0.06)
      ..lineTo(w * 0.60, w * 0.20);
    canvas.drawPath(ears, body);
    canvas.drawOval(Rect.fromLTWH(w * 0.12, w * 0.14, w * 0.76, w * 0.84), body);
    canvas.drawOval(Rect.fromLTWH(w * 0.28, w * 0.50, w * 0.44, w * 0.44), belly);

    final eyeR = w * 0.13;
    for (final cx in [w * 0.36, w * 0.64]) {
      canvas.drawCircle(Offset(cx, w * 0.40), eyeR, white);
      final dy = mood == MascotMood.thinking ? -w * 0.03 : 0.0;
      if (mood == MascotMood.happy) {
        final arc = Rect.fromCircle(center: Offset(cx, w * 0.42), radius: eyeR * 0.55);
        canvas.drawArc(arc, math.pi, math.pi, false, dark
          ..style = PaintingStyle.stroke
          ..strokeWidth = w * 0.03);
        dark.style = PaintingStyle.fill;
      } else {
        canvas.drawCircle(Offset(cx, w * 0.41 + dy), eyeR * 0.5, dark);
        canvas.drawCircle(Offset(cx + eyeR * 0.18, w * 0.37 + dy), eyeR * 0.15, white);
      }
    }
    final b = Path()
      ..moveTo(w * 0.46, w * 0.52)
      ..lineTo(w * 0.54, w * 0.52)
      ..lineTo(w * 0.50, w * 0.62)
      ..close();
    canvas.drawPath(b, beak);
    if (mood == MascotMood.listening) {
      final wave = Paint()
        ..color = scheme.tertiary
        ..style = PaintingStyle.stroke
        ..strokeWidth = w * 0.025;
      for (var i = 1; i <= 2; i++) {
        canvas.drawArc(Rect.fromCircle(center: Offset(w * 0.92, w * 0.40), radius: w * 0.06 * i), -0.8, 1.6, false,
            wave);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _OwlPainter old) => old.mood != mood || old.scheme != scheme;
}
