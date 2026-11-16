#!/bin/bash
# Секреты для локального стека разработки. Не для stage и prod.
set -euo pipefail
cd "$(dirname "$0")/secrets"
gen() { [ -f "$1" ] || python3 -c "import secrets; print(secrets.token_urlsafe(32), end='')" > "$1"; }
gen db_sys_password
gen db_app_password
gen doomich_jwt_secret
gen doomich_invite_pepper
[ -f doomich_master_keys ] || python3 -c "import base64,secrets; print('dev1:'+base64.b64encode(secrets.token_bytes(32)).decode(), end='')" > doomich_master_keys
printf 'postgresql+asyncpg://doomich_app:%s@postgres:5432/doomich' "$(cat db_app_password)" > doomich_database_url
printf 'postgresql+asyncpg://doomich_sys:%s@postgres:5432/doomich' "$(cat db_sys_password)" > doomich_database_sys_url
chmod 600 ./*
echo "секреты разработки готовы"
