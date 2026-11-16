from __future__ import annotations

import struct

import pytest
from fastapi.testclient import TestClient

from doomich_tts.encode import OpusEncoder, ogg_crc, opus_available
from doomich_tts.normalize.en import normalize_en, ordinal_en
from doomich_tts.normalize.numbers_ru import cardinal, decimal, ordinal
from doomich_tts.normalize.ru import normalize_ru
from doomich_tts.stress import StressDict


@pytest.mark.parametrize("n, gender, expected", [
    (0, "m", "ноль"), (1, "m", "один"), (1, "f", "одна"), (2, "f", "две"), (12, "m", "двенадцать"),
    (21, "m", "двадцать один"), (101, "n", "сто одно"), (1000, "m", "одна тысяча"), (2000, "m", "две тысячи"),
    (5000, "m", "пять тысяч"), (21000, "m", "двадцать одна тысяча"), (1_000_000, "m", "один миллион"),
    (2_345_678, "m", "два миллиона триста сорок пять тысяч шестьсот семьдесят восемь"),
])
def test_cardinal(n, gender, expected):
    assert cardinal(n, gender) == expected


@pytest.mark.parametrize("n, gender, case, expected", [
    (1, "m", "nom", "первый"), (2, "f", "nom", "вторая"), (3, "n", "nom", "третье"), (3, "m", "gen", "третьего"),
    (15, "n", "nom", "пятнадцатое"), (40, "m", "nom", "сороковой"), (21, "m", "prep", "двадцать первом"),
    (100, "m", "nom", "сотый"), (2000, "m", "gen", "двухтысячного"),
    (2026, "m", "gen", "две тысячи двадцать шестого"), (2027, "m", "prep", "две тысячи двадцать седьмом"),
    (305, "f", "nom", "триста пятая"),
])
def test_ordinal(n, gender, case, expected):
    assert ordinal(n, gender, case) == expected


def test_decimal():
    assert decimal("3", "14") == "три целых четырнадцать сотых"
    assert decimal("1", "5") == "одна целая пять десятых"
    assert decimal("21", "1") == "двадцать одна целая одна десятая"


@pytest.mark.parametrize("text, expected", [
    ("Экзамен 15.01.2027 в 9:00", "Экзамен пятнадцатое января две тысячи двадцать седьмого года в девять ноль ноль"),
    ("Пара в 10:30 в ауд. 305", "Пара в десять тридцать в аудитория триста пять"),
    ("до 20 декабря", "до двадцатого декабря"),
    ("в 2026 году", "в две тысячи двадцать шестом году"),
    ("Скидка 15%", "Скидка пятнадцать процентов"),
    ("Пройдите 30 м до лестницы", "Пройдите тридцать метров до лестницы"),
    ("Это 1 км, а то 2 км", "Это один километр, а то два километра"),
    ("Длится 1 мин", "Длится одна минута"),
    ("Это 3-я пара, а 5-го числа зачёт", "Это третья пара, а пятого числа зачёт"),
    ("В XXI веке", "В двадцать первом веке"),
    ("Т.е. так и т.д.", "То есть так и так далее"),
    ("Группа ИВТ-21 в МГУ", "Группа и вэ тэ-двадцать один в эм гэ у"),
    ("Пи равно 3,14", "Пи равно три целых четырнадцать сотых"),
    ("Температура -5", "Температура минус пять"),
    ("Стоимость 1 500 ₽", "Стоимость одна тысяча пятьсот рублей"),
    ("ВУЗ и ГОСТ", "вуз и гост"),
])
def test_normalize_ru(text, expected):
    assert normalize_ru(text) == expected


def test_normalize_en():
    assert normalize_en("Class at 9:05, room 12") == "Class at nine oh five, room twelve"
    assert ordinal_en(21) == "twenty-first"
    assert normalize_en("It is 3.14") == "It is three point one four"
    assert normalize_en("50%") == "fifty percent"


def test_stress_dict(tmp_path):
    (tmp_path / "demo.tsv").write_text("корпус\tк+орпус\nсеверный\tс+еверный\n", encoding="utf-8")
    sd = StressDict(tmp_path)
    assert sd.apply("Деканат звонит", style="plus") == "Декан+ат звон+ит"
    assert sd.apply("Северный корпус", "demo", "plus") == "С+еверный к+орпус"
    assert sd.apply("звонит", style="acute") == "звони́т"
    assert sd.apply("звонит", style="none") == "звонит"


def test_ogg_crc_known_value():
    # Контрольное значение CRC-32 Ogg (полином 0x04C11DB7, без отражения) для "123456789"
    assert ogg_crc(b"123456789") == 0x89A1897F


@pytest.mark.skipif(not opus_available(), reason="нет libopus")
def test_ogg_opus_container():
    import numpy as np

    enc = OpusEncoder(24000)
    audio = (0.3 * np.sin(np.linspace(0, 2000, 24000))).astype(np.float32)
    data = enc.encode_ogg(audio)
    assert data[:4] == b"OggS" and b"OpusHead" in data[:64] and b"OpusTags" in data[:200]
    pages = data.count(b"OggS")
    assert pages >= 4
    # Последняя страница помечена флагом конца потока
    last = data.rfind(b"OggS")
    assert data[last + 5] & 0x04
    granule = struct.unpack("<q", data[last + 6 : last + 14])[0]
    assert granule == 50 * 960 + 312


def test_api_synthesize(tmp_path, monkeypatch):
    from doomich_tts.app import create_app, settings

    monkeypatch.setenv("TTS_CACHE_DIR", str(tmp_path / "cache"))
    settings.cache_clear()
    client = TestClient(create_app())
    r = client.post("/v1/synthesize", json={"text": "Привет, это Думыч. Пара в 10:30.", "format": "wav"})
    assert r.status_code == 200 and r.content[:4] == b"RIFF"
    assert float(r.headers["X-Audio-Duration"]) > 0.5
    r2 = client.post("/v1/synthesize", json={"text": "Привет, это Думыч. Пара в 10:30.", "format": "wav"})
    assert r2.content == r.content  # из кэша
    if opus_available():
        r = client.post("/v1/synthesize", json={"text": "Короткая фраза", "format": "ogg_opus"})
        assert r.headers["X-Audio-Format"] == "ogg_opus" and r.content[:4] == b"OggS"
    r = client.post("/v1/normalize", json={"text": "в 2026 году", "lang": "ru"})
    assert r.json()["text"] == "в две тысячи двадцать шестом году"
