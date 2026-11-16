from __future__ import annotations

import base64
import io
import os
import uuid

import pytest

from doomich.common.sqlscript import split_sql
from doomich.security import crypto


def test_keyring_and_user_key_roundtrip():
    ring = crypto.Keyring.parse("a:" + base64.b64encode(b"a" * 32).decode() + ",b:" + base64.b64encode(b"b" * 32).decode())
    assert ring.active_kid == "a"
    uid = uuid.uuid4()
    kid, wrapped = crypto.wrap_user_key(uid, b"k" * 32)
    assert crypto.unwrap_user_key(uid, kid, wrapped) == b"k" * 32
    with pytest.raises(crypto.CryptoError):
        crypto.unwrap_user_key(uuid.uuid4(), kid, wrapped)


def test_cipher_context_binding():
    c = crypto.UserCipher(crypto.new_data_key())
    blob = c.encrypt("секрет", "msg:1")
    assert c.decrypt_str(blob, "msg:1") == "секрет"
    with pytest.raises(crypto.CryptoError):
        c.decrypt(blob, "msg:2")


@pytest.mark.parametrize("size", [0, 10, crypto.FILE_SEGMENT, crypto.FILE_SEGMENT * 2 + 7])
def test_stream_roundtrip(size):
    key = crypto.new_data_key()
    data = os.urandom(size)
    out = io.BytesIO()
    crypto.encrypt_stream(io.BytesIO(data), out, key, "f1")
    out.seek(0)
    assert b"".join(crypto.decrypt_stream(out, key, "f1")) == data


def test_stream_truncation_detected():
    key = crypto.new_data_key()
    out = io.BytesIO()
    crypto.encrypt_stream(io.BytesIO(os.urandom(crypto.FILE_SEGMENT * 2 + 1)), out, key, "f1")
    raw = out.getvalue()
    # Отрезаем последний сегмент: расшифровка должна это заметить
    first_len = int.from_bytes(raw[11:15], "big")
    second_end = 15 + first_len + 4 + int.from_bytes(raw[15 + first_len : 19 + first_len], "big")
    with pytest.raises(crypto.CryptoError):
        b"".join(crypto.decrypt_stream(io.BytesIO(raw[:second_end]), key, "f1"))


def test_split_sql_keeps_dollar_blocks():
    script = """
    CREATE FUNCTION f() RETURNS int LANGUAGE sql AS $$ SELECT 1; $$;
    -- комментарий; с точкой с запятой
    INSERT INTO t VALUES ('a;b');
    DO $body$ BEGIN PERFORM 1; END $body$;
    """
    parts = split_sql(script)
    assert len(parts) == 3
    assert parts[0].endswith("$$ SELECT 1; $$")
    assert "'a;b'" in parts[1]
