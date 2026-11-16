"""Celery: очереди и расписание периодических задач.

Очереди по приоритету: documents (документы), lectures (конспекты, ниже чата
и документов), schedule (синхронизация), maintenance (очистка).
Запуск: celery -A doomich.worker.app worker -Q documents,schedule,maintenance
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from doomich.config import settings

st = settings()
celery_app = Celery("doomich", broker=st.celery_broker_url or st.redis_url, include=["doomich.worker.tasks"])
celery_app.conf.update(
    task_default_queue="documents",
    task_routes={
        "doomich.process_document": {"queue": "documents"},
        "doomich.process_lecture": {"queue": "lectures"},
        "doomich.sync_schedule_source": {"queue": "schedule"},
        "doomich.sync_all_schedules": {"queue": "schedule"},
        "doomich.process_ref_photo": {"queue": "documents"},
        "doomich.*": {"queue": "maintenance"},
    },
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_time_limit=60 * 60,
    task_soft_time_limit=55 * 60,
    timezone="Europe/Moscow",
    broker_connection_retry_on_startup=True,
    task_ignore_result=True,
    beat_schedule={
        "schedule-sync-nightly": {"task": "doomich.sync_all_schedules", "schedule": crontab(hour=5, minute=10)},
        "schedule-sync-daytime": {"task": "doomich.sync_all_schedules", "schedule": crontab(hour="9-20/3", minute=25)},
        "purge-chat-history": {"task": "doomich.purge_history", "schedule": crontab(minute=17)},
        "purge-inactive": {"task": "doomich.purge_inactive", "schedule": crontab(hour=3, minute=40)},
        "purge-sessions": {"task": "doomich.purge_sessions", "schedule": crontab(hour=4, minute=5)},
        "retry-stuck-documents": {"task": "doomich.retry_stuck", "schedule": crontab(minute="*/15")},
    },
)
