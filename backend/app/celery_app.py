from celery import Celery

from app.core.config import settings

REDIS_URL = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ft_lineone",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.scrape_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Santiago",
    enable_utc=True,
    beat_schedule={
        "scrape-all-stores-every-6-hours": {
            "task": "app.tasks.scrape_tasks.scrape_all_stores",
            "schedule": 21600.0,
            "args": (["falabella", "ripley", "paris", "maui", "zara"],),
        },
    },
)
