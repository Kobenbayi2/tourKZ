import os
import subprocess
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from bookings.models import BackupLog
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Создание резервной копии базы данных PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='full',
            choices=['full', 'incremental', 'differential'],
            help='Тип резервной копии'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Удалить старые резервные копии'
        )

    def handle(self, *args, **options):
        backup_type = options['type']
        
        backup_log = BackupLog.objects.create(
            backup_type=backup_type,
            status='in_progress',
            file_path=''
        )
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = settings.BACKUP_DIR
            
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            db_settings = settings.DATABASES['default']
            db_name = db_settings['NAME']
            db_user = db_settings['USER']
            db_password = db_settings['PASSWORD']
            db_host = db_settings['HOST']
            db_port = db_settings['PORT']
            
            filename = f"{db_name}_{backup_type}_{timestamp}.sql"
            filepath = os.path.join(backup_dir, filename)
            
            env = os.environ.copy()
            env['PGPASSWORD'] = db_password
            
            cmd = [
                'pg_dump',
                f'--host={db_host}',
                f'--port={db_port}',
                f'--username={db_user}',
                '--format=custom',
                '--verbose',
                f'--file={filepath}',
                db_name
            ]
            
            self.stdout.write(self.style.SUCCESS(f'Начало создания резервной копии: {filename}'))
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                file_size = os.path.getsize(filepath)
                backup_log.status = 'completed'
                backup_log.file_path = filepath
                backup_log.file_size = file_size
                backup_log.completed_at = datetime.now()
                backup_log.save()
                
                self.stdout.write(self.style.SUCCESS(
                    f'Резервная копия успешно создана: {filename} ({file_size / (1024*1024):.2f} МБ)'
                ))
                logger.info(f'Backup created successfully: {filename}')
            else:
                raise Exception(result.stderr)
        
        except Exception as e:
            backup_log.status = 'failed'
            backup_log.error_message = str(e)
            backup_log.completed_at = datetime.now()
            backup_log.save()
            
            self.stdout.write(self.style.ERROR(f'Ошибка при создании резервной копии: {str(e)}'))
            logger.error(f'Backup failed: {str(e)}')
        
        if options['cleanup']:
            self.cleanup_old_backups()
    
    def cleanup_old_backups(self):
        retention_days = settings.BACKUP_RETENTION_DAYS
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        old_backups = BackupLog.objects.filter(
            started_at__lt=cutoff_date,
            status='completed'
        )
        
        for backup in old_backups:
            try:
                if os.path.exists(backup.file_path):
                    os.remove(backup.file_path)
                    self.stdout.write(self.style.WARNING(f'Удалена старая копия: {backup.file_path}'))
                backup.delete()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка при удалении {backup.file_path}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Очистка завершена. Удалено резервных копий: {old_backups.count()}'))

