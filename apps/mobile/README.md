# Думыч для Android

Мобильное приложение: чат текстом и голосом, расписание, документы, настройки. Общие экраны и логика лежат в `packages/`, здесь только оболочка телефона: нижняя навигация, сканер QR, ссылки `doomich://`, приём файлов через "Поделиться".

```bash
flutter run --dart-define=DOOMICH_SERVER=http://10.0.2.2:8000
```

`10.0.2.2` это адрес компьютера из эмулятора Android. Для реального телефона укажите адрес сервера в сети.

Сборка для RuStore и сайта:

```bash
flutter build apk --release --split-per-abi --dart-define=DOOMICH_SERVER=https://api.example.ru --dart-define=DOOMICH_DISTRIBUTION=rustore
```

Ключ подписи берётся из `android/key.properties` (в CI создаётся из секретов). Google Play Services приложению не нужны.
