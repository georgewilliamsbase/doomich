from __future__ import annotations

import io
import uuid

import pyotp

from tests.conftest import register


async def make_admin(role: str = "superadmin", tenant_id: uuid.UUID | None = None) -> tuple[str, str]:
    from doomich.db import get_db
    from doomich.models import Admin
    from doomich.security.passwords import hash_secret

    login = f"adm{uuid.uuid4().hex[:6]}"
    async with get_db().sys_session() as s:
        s.add(Admin(id=uuid.uuid4(), login=login, password_hash=hash_secret("Admin-Password-123"), role=role,
                    tenant_id=tenant_id))
    return login, "Admin-Password-123"


async def admin_headers(client, role="superadmin", tenant_id=None) -> dict[str, str]:
    login, password = await make_admin(role, tenant_id)
    r = await client.post("/admin/v1/auth/login", json={"login": login, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


async def test_totp_flow_in_prod_like_env(client, database):
    from doomich.config import override_settings

    override_settings(database.model_copy(update={"env": "stage"}))
    login, password = await make_admin()
    r = await client.post("/admin/v1/auth/login", json={"login": login, "password": password})
    body = r.json()
    assert body["totp_setup_required"] and body["otpauth_uri"].startswith("otpauth://")
    code = pyotp.TOTP(body["secret"]).now()
    r = await client.post("/admin/v1/auth/totp/confirm", json={"setup_token": body["setup_token"], "code": code})
    assert r.status_code == 200 and r.json()["token"]
    r = await client.post("/admin/v1/auth/login", json={"login": login, "password": password})
    assert r.json()["error"]["code"] == "totp_required"
    r = await client.post("/admin/v1/auth/login", json={"login": login, "password": password,
                                                        "totp": pyotp.TOTP(body["secret"]).now()})
    assert r.status_code == 200 and r.json()["token"]


async def test_tenant_invites_and_print(client):
    h = await admin_headers(client)
    r = await client.post("/admin/v1/tenants", json={"slug": f"u-{uuid.uuid4().hex[:6]}", "name": "Университет"},
                          headers=h)
    assert r.status_code == 201, r.text
    tid = r.json()["id"]
    g = (await client.post(f"/admin/v1/tenants/{tid}/groups", json={"code": "пм-11"}, headers=h)).json()
    assert g["code"] == "ПМ-11"
    r = await client.post(f"/admin/v1/tenants/{tid}/invite-batches",
                          json={"label": "ПМ-11 осень", "count": 100, "group_id": g["id"]}, headers=h)
    assert r.status_code == 201
    batch, codes = r.json()["batch"], r.json()["codes"]
    assert len(set(codes)) == 100
    pdf = await client.get(f"/admin/v1/invite-batches/{batch['id']}/print.pdf", headers=h)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")

    user = await register(client, codes[0])
    assert user["user"]["group"]["code"] == "ПМ-11"
    listed = (await client.get(f"/admin/v1/tenants/{tid}/invite-batches", headers=h)).json()
    assert listed[0]["stats"]["activations"] == 1

    await client.post(f"/admin/v1/invite-batches/{batch['id']}/revoke", headers=h)
    r = await client.post("/v1/auth/invite/check", json={"code": codes[1]})
    assert r.json()["error"]["code"] == "invite_revoked"

    audit = (await client.get("/admin/v1/audit", headers=h)).json()
    actions = {a["action"] for a in audit}
    assert {"tenant.create", "invites.create", "invites.print", "invites.revoke"} <= actions


async def test_schedule_import_dry_run_and_apply(client, env):
    from openpyxl import Workbook

    h = await admin_headers(client, role="tenant_admin", tenant_id=env.tenant_id)
    wb = Workbook()
    ws = wb.active
    ws.append(["Группа", "День недели", "Неделя", "Начало", "Конец", "Дисциплина", "Аудитория"])
    ws.append(["ИВТ-21", "пн", "все", "08:30", "10:00", "Алгебра", "305"])
    ws.append(["ИВТ-21", "вт", "все", "8.30", "", "Геометрия", "306"])
    ws.append(["ИВТ-21", "ср", "все", "xx", "10:00", "Ошибка", "1"])
    buf = io.BytesIO()
    wb.save(buf)
    files = {"file": ("s.xlsx", buf.getvalue(), "application/octet-stream")}
    r = await client.post(f"/admin/v1/tenants/{env.tenant_id}/schedule/import", files=files,
                          data={"dry_run": "true"}, headers=h)
    rep = r.json()
    assert rep["applied"] is False and rep["errors_total"] == 1 and rep["errors"][0]["row"] == 4
    r = await client.post(f"/admin/v1/tenants/{env.tenant_id}/schedule/import", files=files,
                          data={"dry_run": "false", "force": "true"}, headers=h)
    rep = r.json()
    assert rep["applied"] is True and rep["sync"]["added"] == rep["lessons"] > 0

    # Администратор вуза не видит чужие вузы
    other = await client.get(f"/admin/v1/tenants/{uuid.uuid4()}", headers=h)
    assert other.status_code == 403
    stats = (await client.get(f"/admin/v1/tenants/{env.tenant_id}/stats", headers=h)).json()
    assert stats["users"] == 0


async def test_bindings_route_llm_adapter(client, env):
    from doomich.chats.router import model_version_for
    from doomich.deps import authenticate

    h = await admin_headers(client)
    r = await client.put("/admin/v1/bindings", json={"tenant_id": str(env.tenant_id), "component": "llm_adapter",
                                                     "model_ref": "doomich-lora-test-v1"}, headers=h)
    assert r.status_code == 200, r.text
    user = await register(client, env.codes[0])
    cu = await authenticate(user["tokens"]["access_token"])
    model, version = await model_version_for(cu)
    assert model == "doomich-lora-test-v1" and version.startswith("doomich-lora-test-v1+")


async def test_block_user(client, env):
    h = await admin_headers(client, role="tenant_admin", tenant_id=env.tenant_id)
    user = await register(client, env.codes[0])
    r = await client.post(f"/admin/v1/tenants/{env.tenant_id}/users/block", json={"login": user["login"]}, headers=h)
    assert r.json()["status"] == "blocked"
    assert (await client.get("/v1/me", headers=user["headers"])).status_code == 403


async def test_tenant_settings_reach_client(client, env):
    """Краткое имя и возможности, заданные в панели, клиент видит в /v1/tenant."""
    h = await admin_headers(client)
    r = await client.patch(f"/admin/v1/tenants/{env.tenant_id}", headers=h,
                           json={"short_name": "ТВ", "settings": {"features": {"navigation": True},
                                                                   "support_contact": "help@example.ru"}})
    assert r.status_code == 200, r.text
    user = await register(client, env.codes[0])
    info = (await client.get("/v1/tenant", headers=user["headers"])).json()
    assert info["short_name"] == "ТВ"
    assert info["features"]["navigation"] is True and info["features"]["voice"] is True
    assert info["support_contact"] == "help@example.ru"


async def test_schema_matches_models(database):
    """Модели SQLAlchemy и миграции не должны разъезжаться."""
    from sqlalchemy import text

    from doomich.db import Base, get_db

    async with get_db().sys_session() as s:
        rows = (await s.execute(text(
            "select table_name, column_name from information_schema.columns where table_schema = 'public'"
        ))).all()
    db_cols: dict[str, set[str]] = {}
    for t, c in rows:
        db_cols.setdefault(t, set()).add(c)
    for table in Base.metadata.sorted_tables:
        assert table.name in db_cols, f"таблицы {table.name} нет в миграциях"
        model_cols = {c.name for c in table.columns}
        assert model_cols == db_cols[table.name], f"{table.name}: {model_cols ^ db_cols[table.name]}"

