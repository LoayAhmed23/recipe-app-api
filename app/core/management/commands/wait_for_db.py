"""
Django command to wait for DB to be available
"""
import time

from psycopg2 import OperationalError as Psycopg2Error

from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **opsions):
        """Command Code"""
        self.stdout.write('Waiting for DB....')
        db_up = False
        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2Error, OperationalError):
                self.stdout.write('DB unavailabe sleeping for 1 second')
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS('Database availabe'))
