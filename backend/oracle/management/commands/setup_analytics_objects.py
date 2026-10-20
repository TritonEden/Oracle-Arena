from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Create missing analytics objects, or refresh their snapshots after imports."

    def add_arguments(self, parser):
        parser.add_argument("--refresh", action="store_true", help="Refresh existing objects only")

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("Analytics objects require PostgreSQL.")
        filename = "refresh_analytics_objects.sql" if options["refresh"] else "analytics_objects.sql"
        sql_path = Path(__file__).resolve().parents[3] / "database" / filename
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(sql_path.read_text())
        self.stdout.write(self.style.SUCCESS("Analytics objects refreshed." if options["refresh"]
                                                  else "Missing analytics objects created."))
