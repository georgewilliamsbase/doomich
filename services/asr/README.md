# Сервис распознавания речи

Русский: GigaAM-v3 (MIT), английский: Whisper large-v3-turbo (MIT). Модель выбирается по языку запроса, при `lang=auto` язык определяет Whisper.

| Бэкенд | Когда использовать |
|---|---|
| `sherpa` | основной: ONNX-экспорт GigaAM-v3 (или T-one) через sherpa-onnx, аудио только в памяти, работает на CPU и GPU |
| `gigaam` | оригинальная модель на PyTorch, нужна для сравнения и дообучения |
| `faster_whisper` | английская речь и определение языка |
| `mock` | тесты и разработка без моделей |

```bash
ASR_RU_BACKEND=sherpa ASR_RU_MODEL=/models/asr/gigaam-v3-rnnt ASR_EN_BACKEND=faster_whisper \
  uv run uvicorn --factory doomich_asr.app:create_app --port 8001
```

## API

`POST /v1/transcribe?lang=ru&sample_rate=16000&timestamps=false&tenant=<slug>`, тело PCM16 (`audio/l16`) или WAV. Ответ: `text`, `lang`, `segments` (если просили таймкоды), `duration`, `rtf`.

Длинные записи режутся на куски до 25 секунд по самым тихим местам.

## Профили вузов

`ASR_PROFILES_DIR/<slug>.json` собирает ML-платформа (`dml asr build-profile`). В профиле словарь терминов, таблица исправлений и, если вуз дообучал модель, путь к ней. Сервис держит в памяти до четырёх дообученных моделей.

```json
{"tenant": "demo", "version": "2027-03-01",
 "hotwords": ["матанализ", "деканат"],
 "corrections": {"мат анализ": "матанализ"},
 "model": {"ru": {"backend": "sherpa", "model_dir": "/models/asr/demo-gigaam-ft-v2"}}}
```
