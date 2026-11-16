"""doomich-manage: служебные команды.

  doomich-manage migrate                 применить миграции
  doomich-manage openapi                 напечатать схему OpenAPI
  doomich-manage seed-demo               демо-вуз, группа, расписание и коды приглашения
  doomich-manage create-admin LOGIN --role superadmin [--tenant SLUG]
  doomich-manage create-invites SLUG --count 100 --label "ИВТ-21" [--role student] [--group ИВТ-21]
  doomich-manage gen-master-key          новый мастер-ключ (base64)
  doomich-manage rewrap-keys             перешифровать ключи пользователей активным мастер-ключом
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import secrets
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import select


def _migrate() -> None:
    from alembic import command
    from alembic.config import Config

    root = Path(__file__).resolve().parents[2]
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    command.upgrade(cfg, "head")


def _openapi() -> None:
    from doomich.main import create_app

    print(json.dumps(create_app().openapi(), ensure_ascii=False, indent=2))


async def _seed_demo() -> None:
    from doomich.accounts import invites
    from doomich.config import settings
    from doomich.db import init_db
    from doomich.models import AcademicTerm, Admin, Campus, StudyGroup, Tenant
    from doomich.schedule.records import LessonRecord
    from doomich.schedule.sync import apply_records, manual_source
    from doomich.security.passwords import hash_secret

    db = init_db(settings())
    async with db.sys_session() as s:
        tenant = await s.scalar(select(Tenant).where(Tenant.slug == "demo"))
        if tenant is None:
            tenant = Tenant(id=uuid.uuid4(), slug="demo", name="Демонстрационный университет", short_name="ДемоУ",
                            timezone="Europe/Moscow",
                            settings={"teacher_names_mode": "store", "download_site": "localhost",
                                      "bell_schedule": [["08:30", "10:00"], ["10:10", "11:40"], ["12:20", "13:50"],
                                                        ["14:00", "15:30"], ["15:40", "17:10"]],
                                      "features": {"navigation": True, "courses": True}})
            s.add(tenant)
            await s.flush()
            s.add(Campus(id=uuid.uuid4(), tenant_id=tenant.id, name="Главный кампус", address="ул. Примерная, 1"))
            today = date.today()
            s.add(AcademicTerm(id=uuid.uuid4(), tenant_id=tenant.id, name="Демо-семестр",
                               starts_on=today - timedelta(days=today.weekday() + 14),
                               ends_on=today + timedelta(days=120)))
            await s.flush()
        group = await s.scalar(select(StudyGroup).where(StudyGroup.tenant_id == tenant.id, StudyGroup.code == "ДЕМО-1"))
        if group is None:
            group = StudyGroup(id=uuid.uuid4(), tenant_id=tenant.id, code="ДЕМО-1", name="Демо-группа", year=1,
                               subgroups=["1", "2"])
            s.add(group)
            await s.flush()
        from doomich.common.timeutil import combine_local

        records = []
        start = date.today() - timedelta(days=date.today().weekday())
        plan = [("Математический анализ", "lecture", "305"), ("Программирование", "lab", "214"),
                ("Физика", "practice", "112"), ("История", "lecture", "Актовый зал")]
        for week in range(3):
            for wd in range(5):
                day = start + timedelta(days=week * 7 + wd)
                for i, (subj, kind, room) in enumerate(plan[wd % 2 : wd % 2 + 2]):
                    t0, t1 = (("08:30", "10:00"), ("10:10", "11:40"))[i]
                    records.append(LessonRecord(group="ДЕМО-1", subject=subj, kind=kind, room=room,
                                                starts_at=combine_local(day, t0, tenant.timezone),
                                                ends_at=combine_local(day, t1, tenant.timezone),
                                                teacher="Иванов И. И." if kind == "lecture" else "Петрова А. А."))
        src = await manual_source(s, tenant.id)
        await apply_records(s, tenant=tenant, source=src, records=records, force=True)
        _, codes = await invites.create_batch(s, tenant_id=tenant.id, label="Демо", count=5, group_id=group.id,
                                              max_uses=50)
        _, teacher_codes = await invites.create_batch(s, tenant_id=tenant.id, label="Демо-преподаватели", count=1,
                                                      role="teacher", max_uses=10)
        admin = await s.scalar(select(Admin).where(Admin.login == "admin"))
        password = None
        if admin is None:
            password = os.environ.get("DOOMICH_DEMO_ADMIN_PASSWORD") or secrets.token_urlsafe(12)
            s.add(Admin(id=uuid.uuid4(), login="admin", password_hash=hash_secret(password), role="superadmin"))
    print("Демо-вуз: demo")
    print("Коды приглашения студентов:", ", ".join(codes))
    print("Код приглашения преподавателя:", teacher_codes[0])
    if password:
        print(f"Админ-панель: логин admin, пароль {password}")


async def _create_admin(login: str, role: str, tenant_slug: str | None) -> None:
    from doomich.config import settings
    from doomich.db import init_db
    from doomich.models import Admin, Tenant
    from doomich.security.passwords import hash_secret

    db = init_db(settings())
    password = secrets.token_urlsafe(14)
    async with db.sys_session() as s:
        tenant_id = None
        if tenant_slug:
            tenant_id = await s.scalar(select(Tenant.id).where(Tenant.slug == tenant_slug))
            if tenant_id is None:
                sys.exit(f"вуз {tenant_slug} не найден")
        s.add(Admin(id=uuid.uuid4(), login=login.lower(), password_hash=hash_secret(password), role=role,
                    tenant_id=tenant_id))
    print(f"Администратор {login} создан. Временный пароль: {password}")
    print("При первом входе на stage/prod нужно подключить TOTP.")


async def _create_invites(slug: str, count: int, label: str, role: str, group_code: str | None,
                          max_uses: int, days: int | None) -> None:
    from doomich.accounts import invites
    from doomich.config import settings
    from doomich.db import init_db
    from doomich.models import StudyGroup, Tenant

    db = init_db(settings())
    async with db.sys_session() as s:
        tenant = await s.scalar(select(Tenant).where(Tenant.slug == slug))
        if tenant is None:
            sys.exit(f"вуз {slug} не найден")
        group_id = None
        if group_code:
            group_id = await s.scalar(select(StudyGroup.id).where(StudyGroup.tenant_id == tenant.id,
                                                                   StudyGroup.code == group_code.upper()))
            if group_id is None:
                sys.exit(f"группа {group_code} не найдена")
        _, codes = await invites.create_batch(
            s, tenant_id=tenant.id, label=label, count=count, role=role, group_id=group_id, max_uses=max_uses,
            expires_on=date.today() + timedelta(days=days) if days else None)
    print("\n".join(codes))


async def _rewrap() -> None:
    from doomich.config import settings
    from doomich.db import init_db
    from doomich.models import UserKey
    from doomich.security import crypto

    db = init_db(settings())
    ring = crypto.keyring()
    n = 0
    async with db.sys_session() as s:
        for row in (await s.scalars(select(UserKey).where(UserKey.kid != ring.active_kid))).all():
            key = crypto.unwrap_user_key(row.user_id, row.kid, row.wrapped)
            row.kid, row.wrapped = crypto.wrap_user_key(row.user_id, key)
            n += 1
    print(f"перешифровано ключей: {n}")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="doomich-manage")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("migrate")
    sub.add_parser("openapi")
    sub.add_parser("seed-demo")
    a = sub.add_parser("create-admin")
    a.add_argument("login")
    a.add_argument("--role", default="superadmin", choices=["superadmin", "tenant_admin", "operator"])
    a.add_argument("--tenant")
    inv = sub.add_parser("create-invites")
    inv.add_argument("slug")
    inv.add_argument("--count", type=int, default=10)
    inv.add_argument("--label", default="консоль")
    inv.add_argument("--role", default="student", choices=["student", "teacher", "staff"])
    inv.add_argument("--group")
    inv.add_argument("--max-uses", type=int, default=1)
    inv.add_argument("--days", type=int)
    sub.add_parser("gen-master-key")
    sub.add_parser("rewrap-keys")
    args = p.parse_args(argv)

    if args.cmd == "migrate":
        _migrate()
    elif args.cmd == "openapi":
        _openapi()
    elif args.cmd == "seed-demo":
        asyncio.run(_seed_demo())
    elif args.cmd == "create-admin":
        asyncio.run(_create_admin(args.login, args.role, args.tenant))
    elif args.cmd == "create-invites":
        asyncio.run(_create_invites(args.slug, args.count, args.label, args.role, args.group, args.max_uses,
                                    args.days))
    elif args.cmd == "gen-master-key":
        print(f"k{date.today():%Y%m%d}:" + base64.b64encode(secrets.token_bytes(32)).decode())
    elif args.cmd == "rewrap-keys":
        asyncio.run(_rewrap())


if __name__ == "__main__":
    main()
