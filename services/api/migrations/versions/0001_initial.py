"""Начальная схема R1.0: вузы, расписание, аккаунты, чаты, документы, админка.

Revision ID: 0001
Revises:
Create Date: 2026-11-16
"""

from alembic import op

from doomich.common.sqlscript import run_script

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA = r"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE OR REPLACE FUNCTION app_user() RETURNS uuid LANGUAGE sql STABLE AS
$$ SELECT nullif(current_setting('app.user_id', true), '')::uuid $$;

CREATE OR REPLACE FUNCTION app_tenant() RETURNS uuid LANGUAGE sql STABLE AS
$$ SELECT nullif(current_setting('app.tenant_id', true), '')::uuid $$;

CREATE OR REPLACE FUNCTION app_courses() RETURNS uuid[] LANGUAGE sql STABLE AS
$$ SELECT coalesce(string_to_array(nullif(current_setting('app.course_ids', true), ''), ',')::uuid[], '{}'::uuid[]) $$;

CREATE TABLE tenants (
    id uuid PRIMARY KEY,
    slug varchar(64) NOT NULL UNIQUE,
    name text NOT NULL,
    short_name text,
    timezone text NOT NULL DEFAULT 'Europe/Moscow',
    default_locale varchar(8) NOT NULL DEFAULT 'ru',
    settings jsonb NOT NULL DEFAULT '{}',
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE campuses (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name text NOT NULL,
    address text,
    lat double precision,
    lon double precision,
    settings jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_campuses_tenant ON campuses(tenant_id);

CREATE TABLE academic_terms (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name text NOT NULL,
    starts_on date NOT NULL,
    ends_on date NOT NULL,
    first_week_odd boolean NOT NULL DEFAULT true,
    holidays jsonb NOT NULL DEFAULT '[]',
    CHECK (ends_on >= starts_on)
);
CREATE INDEX ix_terms_tenant ON academic_terms(tenant_id, starts_on);

CREATE TABLE study_groups (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    code text NOT NULL,
    name text,
    faculty text,
    year integer,
    subgroups text[] NOT NULL DEFAULT '{}',
    external_id text,
    is_active boolean NOT NULL DEFAULT true,
    UNIQUE (tenant_id, code)
);

CREATE TABLE teachers (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    key text NOT NULL,
    display_name text,
    external_id text,
    UNIQUE (tenant_id, key)
);

CREATE TABLE rooms (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    campus_id uuid REFERENCES campuses(id) ON DELETE SET NULL,
    building text NOT NULL DEFAULT '',
    number text NOT NULL,
    name text,
    campus_room_id uuid,
    UNIQUE (tenant_id, building, number)
);

CREATE TABLE schedule_sources (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name text NOT NULL,
    kind text NOT NULL,
    config jsonb NOT NULL DEFAULT '{}',
    enabled boolean NOT NULL DEFAULT true,
    require_review_on_spike boolean NOT NULL DEFAULT true,
    last_sync_at timestamptz,
    last_status text,
    last_error text,
    last_count integer,
    pending_snapshot jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE lessons (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    group_id uuid NOT NULL REFERENCES study_groups(id) ON DELETE CASCADE,
    subgroup text,
    subject text NOT NULL,
    kind text NOT NULL DEFAULT 'other',
    starts_at timestamptz NOT NULL,
    ends_at timestamptz NOT NULL,
    room_id uuid REFERENCES rooms(id) ON DELETE SET NULL,
    room_text text,
    teacher_id uuid REFERENCES teachers(id) ON DELETE SET NULL,
    source_id uuid REFERENCES schedule_sources(id) ON DELETE SET NULL,
    ext_key text NOT NULL,
    note text,
    status text NOT NULL DEFAULT 'scheduled',
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, group_id, ext_key),
    CHECK (ends_at > starts_at)
);
CREATE INDEX ix_lessons_group_time ON lessons(tenant_id, group_id, starts_at);
CREATE INDEX ix_lessons_teacher_time ON lessons(tenant_id, teacher_id, starts_at);

CREATE TABLE schedule_changes (
    id bigserial PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    group_id uuid NOT NULL REFERENCES study_groups(id) ON DELETE CASCADE,
    ext_key text NOT NULL,
    change text NOT NULL,
    before jsonb,
    after jsonb,
    lesson_date date NOT NULL,
    detected_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_changes_group ON schedule_changes(tenant_id, group_id, detected_at);

CREATE TABLE users (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    login text NOT NULL,
    login_norm text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    recovery_hash text NOT NULL,
    role text NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'teacher', 'staff')),
    group_id uuid REFERENCES study_groups(id) ON DELETE SET NULL,
    subgroup text,
    locale varchar(8) NOT NULL DEFAULT 'ru',
    history_days integer NOT NULL DEFAULT 90 CHECK (history_days IN (0, 7, 30, 90)),
    is_beta boolean NOT NULL DEFAULT false,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'blocked')),
    created_on date NOT NULL DEFAULT current_date,
    last_active_on date NOT NULL DEFAULT current_date
);
CREATE INDEX ix_users_tenant ON users(tenant_id);

CREATE TABLE user_keys (
    user_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    kid text NOT NULL,
    wrapped bytea NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sessions (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    family_id uuid NOT NULL,
    token_hash bytea NOT NULL UNIQUE,
    platform text,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    rotated_at timestamptz,
    revoked_at timestamptz
);
CREATE INDEX ix_sessions_user ON sessions(user_id);
CREATE INDEX ix_sessions_family ON sessions(family_id);

CREATE TABLE invite_batches (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    label text NOT NULL,
    kind text NOT NULL DEFAULT 'register' CHECK (kind IN ('register', 'role_upgrade')),
    role text NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'teacher', 'staff')),
    group_id uuid REFERENCES study_groups(id) ON DELETE SET NULL,
    is_beta boolean NOT NULL DEFAULT false,
    max_uses integer NOT NULL DEFAULT 1 CHECK (max_uses > 0),
    expires_on date,
    code_count integer NOT NULL DEFAULT 0,
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE invite_codes (
    id uuid PRIMARY KEY,
    batch_id uuid NOT NULL REFERENCES invite_batches(id) ON DELETE CASCADE,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    code_hash bytea NOT NULL UNIQUE,
    code_enc bytea NOT NULL,
    uses integer NOT NULL DEFAULT 0,
    max_uses integer NOT NULL DEFAULT 1,
    expires_on date,
    revoked boolean NOT NULL DEFAULT false
);
CREATE INDEX ix_invite_codes_batch ON invite_codes(batch_id);

CREATE TABLE chats (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    title_enc bytea,
    document_ids uuid[] NOT NULL DEFAULT '{}',
    lecture_id uuid,
    course_id uuid,
    summary_enc bytea,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_chats_user ON chats(user_id, updated_at DESC);

CREATE TABLE messages (
    id uuid PRIMARY KEY,
    chat_id uuid NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role text NOT NULL CHECK (role IN ('user', 'assistant')),
    content_enc bytea NOT NULL,
    sources_enc bytea,
    mode text NOT NULL DEFAULT 'text',
    model_version text,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_messages_chat ON messages(chat_id, created_at);
CREATE INDEX ix_messages_user_time ON messages(user_id, created_at);

CREATE TABLE feedback (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    rating smallint NOT NULL CHECK (rating IN (-1, 1)),
    comment text,
    category text,
    model_version text,
    mode text,
    question text,
    answer text,
    created_on date NOT NULL DEFAULT current_date
);

CREATE TABLE documents (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    scope text NOT NULL DEFAULT 'personal' CHECK (scope IN ('personal', 'kb', 'course', 'lecture')),
    course_id uuid,
    title_enc bytea,
    title text,
    mime text NOT NULL,
    kind text NOT NULL,
    size_bytes bigint NOT NULL,
    pages integer,
    status text NOT NULL DEFAULT 'uploaded',
    error text,
    storage_key text,
    file_key_wrapped bytea,
    valid_as_of date,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_documents_user ON documents(user_id);
CREATE INDEX ix_documents_scope ON documents(tenant_id, scope);

CREATE TABLE chunks (
    id uuid PRIMARY KEY,
    document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id uuid,
    scope text NOT NULL,
    course_id uuid,
    ord integer NOT NULL,
    page integer,
    sheet text,
    section text,
    body text NOT NULL,
    tokens integer NOT NULL DEFAULT 0,
    embedding vector(1024),
    fts tsvector GENERATED ALWAYS AS (
        to_tsvector('russian', coalesce(section, '') || ' ' || body) || to_tsvector('english', body)
    ) STORED,
    meta jsonb NOT NULL DEFAULT '{}'
);
CREATE INDEX ix_chunks_document ON chunks(document_id, ord);
CREATE INDEX ix_chunks_user ON chunks(user_id);
CREATE INDEX ix_chunks_scope ON chunks(tenant_id, scope);
CREATE INDEX ix_chunks_fts ON chunks USING gin(fts);
CREATE INDEX ix_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE TABLE admins (
    id uuid PRIMARY KEY,
    login text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    totp_secret_enc bytea,
    totp_enabled boolean NOT NULL DEFAULT false,
    role text NOT NULL CHECK (role IN ('superadmin', 'tenant_admin', 'operator')),
    tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE,
    disabled boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    last_login_at timestamptz
);

CREATE TABLE admin_audit (
    id bigserial PRIMARY KEY,
    admin_id uuid,
    tenant_id uuid,
    action text NOT NULL,
    object_type text,
    object_id text,
    details jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_audit_time ON admin_audit(created_at DESC);

CREATE TABLE model_bindings (
    id uuid PRIMARY KEY,
    tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE,
    campus_id uuid REFERENCES campuses(id) ON DELETE CASCADE,
    component text NOT NULL,
    model_ref text NOT NULL,
    params jsonb NOT NULL DEFAULT '{}',
    stage text NOT NULL DEFAULT 'production' CHECK (stage IN ('canary', 'production')),
    traffic_pct integer NOT NULL DEFAULT 100 CHECK (traffic_pct BETWEEN 0 AND 100),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_bindings_scope ON model_bindings(component, tenant_id, campus_id);

CREATE TABLE app_releases (
    id uuid PRIMARY KEY,
    app text NOT NULL CHECK (app IN ('mobile', 'desktop')),
    platform text NOT NULL,
    channel text NOT NULL DEFAULT 'stable' CHECK (channel IN ('stable', 'beta')),
    version text NOT NULL,
    build integer NOT NULL,
    url text NOT NULL,
    sha256 text NOT NULL,
    signature text,
    min_supported_build integer NOT NULL DEFAULT 0,
    notes_ru text,
    notes_en text,
    published_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (app, platform, channel, build)
);

CREATE TABLE usage_counters (
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period text NOT NULL,
    metric text NOT NULL,
    value bigint NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, period, metric)
);
"""

# Row-Level Security. Политики действуют на роль doomich_app (у doomich_sys BYPASSRLS).
RLS = r"""
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_tenants_read ON tenants FOR SELECT USING (id = app_tenant());

ALTER TABLE campuses ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_campuses_read ON campuses FOR SELECT USING (tenant_id = app_tenant());

ALTER TABLE academic_terms ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_terms_read ON academic_terms FOR SELECT USING (tenant_id = app_tenant());

ALTER TABLE study_groups ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_groups_read ON study_groups FOR SELECT USING (tenant_id = app_tenant());

ALTER TABLE teachers ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_teachers_read ON teachers FOR SELECT USING (tenant_id = app_tenant());

ALTER TABLE rooms ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_rooms_read ON rooms FOR SELECT USING (tenant_id = app_tenant());

ALTER TABLE lessons ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_lessons_read ON lessons FOR SELECT USING (tenant_id = app_tenant());

ALTER TABLE schedule_changes ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_changes_read ON schedule_changes FOR SELECT USING (tenant_id = app_tenant());

ALTER TABLE schedule_sources ENABLE ROW LEVEL SECURITY;

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_users_self ON users FOR SELECT USING (id = app_user());
CREATE POLICY p_users_update ON users FOR UPDATE USING (id = app_user()) WITH CHECK (id = app_user());

ALTER TABLE user_keys ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_user_keys_self ON user_keys FOR SELECT USING (user_id = app_user());

ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE invite_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE invite_codes ENABLE ROW LEVEL SECURITY;

ALTER TABLE chats ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_chats_owner ON chats USING (user_id = app_user())
    WITH CHECK (user_id = app_user() AND tenant_id = app_tenant());

ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_messages_owner ON messages USING (user_id = app_user()) WITH CHECK (user_id = app_user());

ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_feedback_insert ON feedback FOR INSERT WITH CHECK (tenant_id = app_tenant());

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_documents_read ON documents FOR SELECT USING (
    user_id = app_user()
    OR (scope = 'kb' AND tenant_id = app_tenant())
    OR (scope = 'course' AND course_id = ANY (app_courses()))
);
CREATE POLICY p_documents_insert ON documents FOR INSERT
    WITH CHECK (user_id = app_user() AND tenant_id = app_tenant() AND scope IN ('personal', 'lecture'));
CREATE POLICY p_documents_update ON documents FOR UPDATE USING (user_id = app_user()) WITH CHECK (user_id = app_user());
CREATE POLICY p_documents_delete ON documents FOR DELETE USING (user_id = app_user());

ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_chunks_read ON chunks FOR SELECT USING (
    user_id = app_user()
    OR (scope = 'kb' AND tenant_id = app_tenant())
    OR (scope = 'course' AND course_id = ANY (app_courses()))
);

ALTER TABLE admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_bindings ENABLE ROW LEVEL SECURITY;

ALTER TABLE usage_counters ENABLE ROW LEVEL SECURITY;
CREATE POLICY p_usage_owner ON usage_counters USING (user_id = app_user()) WITH CHECK (user_id = app_user());
"""

# Права выдаются, только если роли уже созданы (их создаёт init-скрипт БД, не миграция).
GRANTS = r"""
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'doomich_app') THEN
    GRANT USAGE ON SCHEMA public TO doomich_app;
    GRANT SELECT ON tenants, campuses, academic_terms, study_groups, teachers, rooms,
                    lessons, schedule_changes, app_releases TO doomich_app;
    GRANT SELECT (id, tenant_id, login, role, group_id, subgroup, locale, history_days,
                  is_beta, status, created_on, last_active_on) ON users TO doomich_app;
    GRANT UPDATE (locale, group_id, subgroup, history_days, last_active_on) ON users TO doomich_app;
    GRANT SELECT ON user_keys TO doomich_app;
    GRANT SELECT, INSERT, UPDATE, DELETE ON chats, messages, documents, usage_counters TO doomich_app;
    GRANT INSERT ON feedback TO doomich_app;
    GRANT SELECT ON chunks TO doomich_app;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'doomich_sys') THEN
    GRANT USAGE ON SCHEMA public TO doomich_sys;
    GRANT ALL ON ALL TABLES IN SCHEMA public TO doomich_sys;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO doomich_sys;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO doomich_sys;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO doomich_sys;
  END IF;
END
$$;
"""


def upgrade() -> None:
    run_script(op, SCHEMA)
    run_script(op, RLS)
    run_script(op, GRANTS)


def downgrade() -> None:
    for table in [
        "usage_counters", "app_releases", "model_bindings", "admin_audit", "admins", "chunks",
        "documents", "feedback", "messages", "chats", "invite_codes", "invite_batches", "sessions",
        "user_keys", "users", "schedule_changes", "lessons", "schedule_sources", "rooms", "teachers",
        "study_groups", "academic_terms", "campuses", "tenants",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    op.execute("DROP FUNCTION IF EXISTS app_user(), app_tenant(), app_courses()")
