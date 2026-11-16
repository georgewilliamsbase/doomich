#!/bin/bash
# Первичная настройка БД (выполняется один раз при создании тома).
# doomich_sys: владелец схемы, BYPASSRLS, миграции и воркеры.
# doomich_app: API, работает только через политики RLS.
set -euo pipefail
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE ROLE doomich_sys LOGIN BYPASSRLS PASSWORD '$(cat /run/secrets/db_sys_password)';
  CREATE ROLE doomich_app LOGIN NOBYPASSRLS PASSWORD '$(cat /run/secrets/db_app_password)';
  ALTER DATABASE "$POSTGRES_DB" OWNER TO doomich_sys;
  GRANT ALL ON SCHEMA public TO doomich_sys;
  ALTER SCHEMA public OWNER TO doomich_sys;
  CREATE EXTENSION IF NOT EXISTS vector;
EOSQL
