import os
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Восстановление базы данных из резервной копии'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Путь к файлу резервной копии'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Очистить базу данных перед восстановлением'
        )

    def handle(self, *args, **options):
        backup_file = options['backup_file']
        clean = options['clean']
        
        if not os.path.exists(backup_file):
            self.stdout.write(self.style.ERROR(f'Файл не найден: {backup_file}'))
            return
        
        try:
            db_settings = settings.DATABASES['default']
            db_name = db_settings['NAME']
            db_user = db_settings['USER']
            db_password = db_settings['PASSWORD']
            db_host = db_settings['HOST']
            db_port = db_settings['PORT']
            
            env = os.environ.copy()
            env['PGPASSWORD'] = db_password
            
            cmd = [
                'pg_restore',
                f'--host={db_host}',
                f'--port={db_port}',
                f'--username={db_user}',
                '--verbose',
                f'--dbname={db_name}'
            ]
            
            if clean:
                cmd.append('--clean')
            
            cmd.append(backup_file)
            
            self.stdout.write(self.style.WARNING(
                f'Начало восстановления базы данных из: {backup_file}'
            ))
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS('База данных успешно восстановлена!'))
                logger.info(f'Database restored from: {backup_file}')
            else:
                raise Exception(result.stderr)
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при восстановлении: {str(e)}'))
            logger.error(f'Restore failed: {str(e)}')

