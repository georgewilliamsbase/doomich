from __future__ import annotations

import uuid

from sqlalchemy import select

from tests.conftest import register


async def test_invite_check_and_register(client, env):
    r = await client.post("/v1/auth/invite/check", json={"code": env.codes[0].lower().replace("-", "")})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == "student"
    assert body["group"]["code"] == "ИВТ-21"

    data = await register(client, env.codes[0])
    assert len(data["recovery_code"].replace("-", "")) == 20
    assert data["user"]["group"]["code"] == "ИВТ-21"
    assert data["user"]["tenant"]["slug"] == env.slug

    # Код одноразовый
    r = await client.post("/v1/auth/invite/check", json={"code": env.codes[0]})
    assert r.json()["error"]["code"] == "invite_used_up"

    me = await client.get("/v1/me", headers=data["headers"])
    assert me.status_code == 200
    assert me.json()["login"] == data["login"]


async def test_register_rejects_bad_input(client, env):
    r = await client.post("/v1/auth/register", json={"invite_code": env.codes[1], "login": "ab",
                                                     "password": "Kosmos-Galaktika-42"})
    assert r.status_code == 422
    r = await client.post("/v1/auth/register", json={"invite_code": env.codes[1], "login": "Нормальный",
                                                     "password": "1234567890"})
    assert r.json()["error"]["code"] == "password_weak"
    r = await client.post("/v1/auth/register", json={"invite_code": "ZZZZ-ZZZZ", "login": "Нормальный2",
                                                     "password": "Kosmos-Galaktika-42"})
    assert r.json()["error"]["code"] == "invite_invalid"


async def test_login_taken_and_name_warning(client, env):
    data = await register(client, env.codes[0], login="ТихийЕнот42")
    r = await client.get("/v1/auth/login-check", params={"login": "тихийенот42"})
    assert r.json() == {"valid": True, "available": False, "problems": [], "warnings": []}
    r = await client.get("/v1/auth/login-check", params={"login": "ИванПетров"})
    assert "looks_like_name" in r.json()["warnings"]
    r = await client.post("/v1/auth/register", json={"invite_code": env.codes[1], "login": "ТихийЕнот42",
                                                     "password": "Kosmos-Galaktika-42"})
    assert r.json()["error"]["code"] == "login_taken"
    assert data["user"]["login"] == "ТихийЕнот42"


async def test_login_refresh_rotation_and_reuse(client, env):
    data = await register(client, env.codes[0])
    r = await client.post("/v1/auth/login", json={"login": data["login"].upper(), "password": data["password"]})
    assert r.status_code == 200, r.text
    refresh1 = r.json()["tokens"]["refresh_token"]

    r = await client.post("/v1/auth/refresh", json={"refresh_token": refresh1})
    assert r.status_code == 200
    refresh2 = r.json()["tokens"]["refresh_token"] if "tokens" in r.json() else r.json()["refresh_token"]
    access2 = r.json()["access_token"]
    assert (await client.get("/v1/me", headers={"Authorization": f"Bearer {access2}"})).status_code == 200

    # Повтор старого токена сразу после ротации считается гонкой
    r = await client.post("/v1/auth/refresh", json={"refresh_token": refresh1})
    assert r.json()["error"]["code"] == "refresh_in_progress"

    # Через окно ожидания повтор старого токена отзывает всю цепочку
    from doomich.common.timeutil import utcnow
    from doomich.db import get_db
    from doomich.models import Session
    from doomich.security.tokens import hash_refresh

    async with get_db().sys_session() as s:
        sess = await s.scalar(select(Session).where(Session.token_hash == hash_refresh(refresh1)))
        sess.rotated_at = utcnow().replace(year=2020)
    r = await client.post("/v1/auth/refresh", json={"refresh_token": refresh1})
    assert r.json()["error"]["code"] == "refresh_reused"
    r = await client.post("/v1/auth/refresh", json={"refresh_token": refresh2})
    assert r.status_code == 401
    assert (await client.get("/v1/me", headers={"Authorization": f"Bearer {access2}"})).status_code == 401


async def test_bad_password_and_rate_limit(client, env):
    data = await register(client, env.codes[0])
    for _ in range(5):
        r = await client.post("/v1/auth/login", json={"login": data["login"], "password": "wrong-password"})
        assert r.status_code == 401
    r = await client.post("/v1/auth/login", json={"login": data["login"], "password": data["password"]})
    assert r.status_code == 429


async def test_logout_revokes(client, env):
    data = await register(client, env.codes[0])
    r = await client.post("/v1/auth/logout", json={"refresh_token": data["tokens"]["refresh_token"]})
    assert r.status_code == 204
    assert (await client.get("/v1/me", headers=data["headers"])).status_code == 401


async def test_recover_with_code(client, env):
    data = await register(client, env.codes[0])
    r = await client.post("/v1/auth/recover", json={"login": data["login"],
                                                    "recovery_code": data["recovery_code"].lower(),
                                                    "new_password": "Novyi-Parol-Dlinnyi-1"})
    assert r.status_code == 200, r.text
    assert r.json()["recovery_code"] != data["recovery_code"]
    # Старые сессии отозваны, старый код восстановления больше не работает
    assert (await client.get("/v1/me", headers=data["headers"])).status_code == 401
    r = await client.post("/v1/auth/recover", json={"login": data["login"], "recovery_code": data["recovery_code"],
                                                    "new_password": "Eshe-Odin-Parol-2"})
    assert r.status_code == 401
    r = await client.post("/v1/auth/login", json={"login": data["login"], "password": "Novyi-Parol-Dlinnyi-1"})
    assert r.status_code == 200


async def test_patch_me_and_group(client, env):
    data = await register(client, env.teacher_codes[0])
    assert data["user"]["role"] == "teacher"
    assert data["user"]["group"] is None
    r = await client.patch("/v1/me", json={"group_id": str(env.group_id), "subgroup": "2", "history_days": 30,
                                           "locale": "en"}, headers=data["headers"])
    assert r.status_code == 200, r.text
    assert r.json()["group"]["code"] == "ИВТ-21"
    assert r.json()["history_days"] == 30
    r = await client.patch("/v1/me", json={"group_id": str(uuid.uuid4())}, headers=data["headers"])
    assert r.status_code == 404
    r = await client.patch("/v1/me", json={"clear_group": True}, headers=data["headers"])
    assert r.json()["group"] is None


async def test_delete_account_removes_everything(client, env):
    from doomich.db import get_db
    from doomich.models import User, UserKey

    data = await register(client, env.codes[0])
    user_id = uuid.UUID(data["user"]["id"])
    r = await client.request("DELETE", "/v1/account", json={"password": "wrong"}, headers=data["headers"])
    assert r.status_code == 401
    r = await client.request("DELETE", "/v1/account", json={"password": data["password"]}, headers=data["headers"])
    assert r.status_code == 204
    async with get_db().sys_session() as s:
        assert await s.get(User, user_id) is None
        assert await s.get(UserKey, user_id) is None
    assert (await client.get("/v1/me", headers=data["headers"])).status_code == 401


async def test_qr_login(client, env):
    phone = await register(client, env.codes[0])
    r = await client.post("/v1/auth/qr/start")
    token = r.json()["token"]
    r = await client.post("/v1/auth/qr/poll", json={"token": token})
    assert r.json() is None
    r = await client.post("/v1/auth/qr/approve", json={"token": token}, headers=phone["headers"])
    assert r.status_code == 204
    r = await client.post("/v1/auth/qr/poll", json={"token": token})
    assert r.json()["user"]["login"] == phone["login"]
    r = await client.post("/v1/auth/qr/poll", json={"token": token})
    assert r.json()["error"]["code"] == "qr_expired"


async def test_role_upgrade_code(client, env):
    from doomich.accounts import invites
    from doomich.db import get_db

    async with get_db().sys_session() as s:
        _, codes = await invites.create_batch(s, tenant_id=env.tenant_id, label="кафедра", count=1, role="teacher",
                                              kind="role_upgrade")
    student = await register(client, env.codes[0])
    # Код повышения роли не годится для регистрации
    r = await client.post("/v1/auth/register", json={"invite_code": codes[0], "login": "Ктото123",
                                                     "password": "Kosmos-Galaktika-42"})
    assert r.json()["error"]["code"] == "invite_wrong_kind"
    r = await client.post("/v1/me/role-upgrade", json={"code": codes[0]}, headers=student["headers"])
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "teacher"
