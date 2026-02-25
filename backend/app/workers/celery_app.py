"""Celery App Configuration"""
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "codigo_red_worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
