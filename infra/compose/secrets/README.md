# Секреты для docker compose

Файлы в этом каталоге не попадают в git. На сервере их раскладывает Ansible из зашифрованного SOPS-файла (`infra/ansible/group_vars/<окружение>/secrets.sops.yaml`). Для разработки их создаёт `make dev` (скрипт `infra/compose/dev-secrets.sh`).

| Файл | Что это |
|---|---|
| `db_sys_password`, `db_app_password` | пароли ролей PostgreSQL |
| `doomich_jwt_secret` | секрет подписи токенов |
| `doomich_master_keys` | мастер-ключи шифрования `kid:base64,...` (`doomich-manage gen-master-key`) |
| `doomich_invite_pepper` | перец для хэшей кодов приглашения |
| `doomich_database_url`, `doomich_database_sys_url` | строки подключения с паролями |
