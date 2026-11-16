from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, update

from doomich.accounts import invites, service
from doomich.accounts.schemas import (
    AuthOut,
    GroupBrief,
    InviteCheckIn,
    InviteCheckOut,
    LoginCheckOut,
    LoginIn,
    MeOut,
    MePatch,
    PasswordChangeIn,
    PasswordIn,
    QrApproveIn,
    QrPollIn,
    QrStartOut,
    RecoverIn,
    RecoverOut,
    RecoveryCodeOut,
    RefreshIn,
    RegisterIn,
    RegisterOut,
    RoleUpgradeIn,
    SessionOut,
    TenantBrief,
    Tokens,
)
from doomich.common.errors import NotFound
from doomich.db import get_db
from doomich.deps import CurrentUser, current_user
from doomich.models import StudyGroup, Tenant, User
from doomich.security import kv

router = APIRouter(prefix="/v1", tags=["accounts"])


def client_key(request: Request) -> str:
    """Ключ клиента для лимитов. IP только хэшируется и нигде не сохраняется."""
    ip = request.headers.get("x-real-ip") or (request.client.host if request.client else "unknown")
    return ip


@router.post("/auth/invite/check", response_model=InviteCheckOut)
async def check_invite(body: InviteCheckIn, request: Request) -> InviteCheckOut:
    await kv.hit(f"invite-check:{kv.anon(client_key(request))}", 30, 600)
    async with get_db().sys_session() as s:
        info = await invites.find_valid(s, body.code)
        tenant = await s.get(Tenant, info.batch.tenant_id)
        assert tenant is not None
        group = await s.get(StudyGroup, info.batch.group_id) if info.batch.group_id else None
        return InviteCheckOut(
            tenant=TenantBrief(id=tenant.id, slug=tenant.slug, name=tenant.name, short_name=tenant.short_name,
                               timezone=tenant.timezone),
            role=info.batch.role,
            group=GroupBrief(id=group.id, code=group.code, name=group.name) if group else None,
        )


@router.get("/auth/login-check", response_model=LoginCheckOut)
async def login_check(request: Request, login: str = Query(min_length=1, max_length=64)) -> LoginCheckOut:
    await kv.hit(f"login-check:{kv.anon(client_key(request))}", 60, 600)
    problems = service.login_problems(login)
    available = not problems and await service.login_available(login)
    return LoginCheckOut(valid=not problems, available=available, problems=problems,
                         warnings=service.login_warnings(login))


@router.post("/auth/register", response_model=RegisterOut, status_code=201)
async def register(body: RegisterIn, request: Request) -> RegisterOut:
    await kv.hit(f"register:{kv.anon(client_key(request))}", 10, 3600)
    tokens, me, recovery = await service.register(
        invite_code=body.invite_code, login=body.login, password=body.password, locale=body.locale,
        platform=body.platform,
    )
    return RegisterOut(tokens=tokens, user=me, recovery_code=recovery)


@router.post("/auth/login", response_model=AuthOut)
async def login(body: LoginIn, request: Request) -> AuthOut:
    tokens, me = await service.login(login=body.login, password=body.password, platform=body.platform,
                                     client_key=client_key(request))
    return AuthOut(tokens=tokens, user=me)


@router.post("/auth/refresh", response_model=Tokens)
async def refresh(body: RefreshIn) -> Tokens:
    return await service.refresh(body.refresh_token)


@router.post("/auth/logout", status_code=204)
async def logout(body: RefreshIn) -> None:
    await service.logout(body.refresh_token)


@router.post("/auth/recover", response_model=RecoverOut)
async def recover(body: RecoverIn, request: Request) -> RecoverOut:
    tokens, me, code = await service.recover(
        login=body.login, recovery_code=body.recovery_code, new_password=body.new_password,
        platform=body.platform, client_key=client_key(request),
    )
    return RecoverOut(tokens=tokens, user=me, recovery_code=code)


@router.post("/auth/qr/start", response_model=QrStartOut)
async def qr_start(request: Request) -> QrStartOut:
    await kv.hit(f"qr-start:{kv.anon(client_key(request))}", 30, 600)
    return QrStartOut(token=await service.qr_start(), expires_in=service.QR_TTL)


@router.post("/auth/qr/approve", status_code=204)
async def qr_approve(body: QrApproveIn, user: CurrentUser = Depends(current_user)) -> None:
    await service.qr_approve(body.token, user.id)


@router.post("/auth/qr/poll", response_model=AuthOut | None)
async def qr_poll(body: QrPollIn, request: Request) -> AuthOut | None:
    await kv.hit(f"qr-poll:{kv.anon(client_key(request))}", 200, 600)
    result = await service.qr_poll(body.token)
    if result is None:
        return None
    return AuthOut(tokens=result[0], user=result[1])


@router.get("/me", response_model=MeOut)
async def get_me(user: CurrentUser = Depends(current_user)) -> MeOut:
    async with get_db().sys_session() as s:
        row = await s.get(User, user.id)
        if row is None:
            raise NotFound()
        return await service.me_out(s, row)


@router.patch("/me", response_model=MeOut)
async def patch_me(body: MePatch, user: CurrentUser = Depends(current_user)) -> MeOut:
    values: dict[str, object] = {}
    if body.locale is not None:
        values["locale"] = body.locale
    if body.history_days is not None:
        values["history_days"] = body.history_days
    if body.clear_group:
        values["group_id"] = None
        values["subgroup"] = None
    elif body.group_id is not None:
        async with get_db().tenant_session(user.tenant_id) as s:
            group = await s.scalar(select(StudyGroup.id).where(StudyGroup.id == body.group_id))
        if group is None:
            raise NotFound("группа не найдена", code="group_not_found")
        values["group_id"] = body.group_id
        values["subgroup"] = body.subgroup
    elif body.subgroup is not None:
        values["subgroup"] = body.subgroup or None
    if values:
        async with get_db().user_session(user.id, user.tenant_id) as s:
            await s.execute(update(User).where(User.id == user.id).values(**values))
    return await get_me(user)


@router.post("/me/password", status_code=204)
async def change_password(body: PasswordChangeIn, user: CurrentUser = Depends(current_user)) -> None:
    await service.change_password(user.id, body.old_password, body.new_password, user.session_id)


@router.post("/me/recovery-code", response_model=RecoveryCodeOut)
async def regenerate_recovery(body: PasswordIn, user: CurrentUser = Depends(current_user)) -> RecoveryCodeOut:
    return RecoveryCodeOut(recovery_code=await service.new_recovery_code(user.id, body.password))


@router.get("/me/sessions", response_model=list[SessionOut])
async def sessions(user: CurrentUser = Depends(current_user)) -> list[SessionOut]:
    rows = await service.list_sessions(user.id)
    return [SessionOut(id=r.id, platform=r.platform, created_on=r.created_at.date(),
                       current=r.id == user.session_id) for r in rows]


@router.delete("/me/sessions/{session_id}", status_code=204)
async def end_session(session_id: str, user: CurrentUser = Depends(current_user)) -> None:
    rows = await service.list_sessions(user.id)
    target = next((r for r in rows if str(r.id) == session_id), None)
    if target is None:
        raise NotFound()
    await service.logout_session(target.id)


@router.post("/me/role-upgrade", response_model=MeOut)
async def role_upgrade(body: RoleUpgradeIn, user: CurrentUser = Depends(current_user)) -> MeOut:
    await service.role_upgrade(user.id, body.code)
    return await get_me(user)


@router.delete("/account", status_code=204)
async def delete_account(body: PasswordIn, user: CurrentUser = Depends(current_user)) -> None:
    await service.delete_account(user.id, body.password)
