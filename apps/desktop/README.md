# Думыч для Windows и Linux

Приложение для ПК: две панели (чаты и диалог), боковая навигация, голосовой ввод удержанием Ctrl+Пробел (работает и при свёрнутом окне на Windows и Linux X11), вход по QR с телефона, самообновление.

```bash
flutter run -d linux --dart-define=DOOMICH_SERVER=http://localhost:8000
```

Сочетания клавиш: Ctrl+N новый чат, Ctrl+M включить или выключить микрофон, Ctrl+, настройки, Enter отправить.

Для сборки на Linux нужны пакеты `libgtk-3-dev libsecret-1-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libkeybinder-3.0-dev`, для записи звука `pulseaudio-utils`. Пакеты deb, rpm и AppImage собирает CI, установщик Windows делается через Inno Setup (`installer/doomich.iss`).
