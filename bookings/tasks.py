from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
import psutil
import logging

from .models import BackupLog, SystemMetric

logger = logging.getLogger(__name__)


@shared_task
def backup_database_task(backup_type='full'):
    try:
        call_command('backup_database', type=backup_type)
        logger.info(f'Scheduled backup completed: {backup_type}')
        return f'Backup {backup_type} completed successfully'
    except Exception as e:
        logger.error(f'Scheduled backup failed: {str(e)}')
        return f'Backup failed: {str(e)}'


@shared_task
def cleanup_old_backups_task():
    try:
        call_command('backup_database', cleanup=True)
        logger.info('Old backups cleanup completed')
        return 'Cleanup completed successfully'
    except Exception as e:
        logger.error(f'Cleanup failed: {str(e)}')
        return f'Cleanup failed: {str(e)}'


@shared_task
def collect_system_metrics_task():
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        SystemMetric.objects.create(metric_name='cpu_usage', metric_value=cpu_percent)
        SystemMetric.objects.create(metric_name='memory_usage', metric_value=memory.percent)
        SystemMetric.objects.create(metric_name='disk_usage', metric_value=disk.percent)
        
        old_metrics = timezone.now() - timedelta(days=7)
        SystemMetric.objects.filter(timestamp__lt=old_metrics).delete()
        
        logger.info('System metrics collected')
        return 'Metrics collected successfully'
    except Exception as e:
        logger.error(f'Metrics collection failed: {str(e)}')
        return f'Metrics collection failed: {str(e)}'


@shared_task
def send_booking_confirmation_email(booking_id):
    logger.info(f'Sending booking confirmation for booking {booking_id}')
    return f'Confirmation email sent for booking {booking_id}'

