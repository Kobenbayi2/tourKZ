import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tour.settings')

app = Celery('tour')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'backup-database-daily': {
        'task': 'bookings.tasks.backup_database_task',
        'schedule': crontab(hour=2, minute=0),
    },
    'cleanup-old-backups': {
        'task': 'bookings.tasks.cleanup_old_backups_task',
        'schedule': crontab(hour=3, minute=0),
    },
    'collect-system-metrics': {
        'task': 'bookings.tasks.collect_system_metrics_task',
        'schedule': crontab(minute='*/5'),
    },
}

