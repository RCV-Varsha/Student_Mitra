import time
from django.core.management.base import BaseCommand
from django.db import close_old_connections, OperationalError
from study.models import Heartbeat
from study.jobs import claim_job, process_job
class Command(BaseCommand):
    help='Run the persistent database-backed PDF worker'
    def add_arguments(self,p):p.add_argument('--once',action='store_true')
    def handle(self,*args,**options):
        while True:
            try:
                close_old_connections()
                Heartbeat.objects.update_or_create(name='pdf-worker',defaults={})
                job=claim_job()
                if job:process_job(job)
                if options['once']:return
                if not job:time.sleep(2)
            except OperationalError:
                self.stderr.write('Database temporarily unavailable; reconnecting in 5 seconds.')
                close_old_connections()
                if options['once']:raise
                time.sleep(5)
