import logging
import shutil
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from separator.models import Task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Delete tasks older than 24 hours and their associated files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--max-age-hours",
            type=int,
            default=24,
            help="Max age in hours (default: 24)",
        )

    def handle(self, *args, **options):
        max_age = options["max_age_hours"]
        cutoff = timezone.now() - timedelta(hours=max_age)
        old_tasks = Task.objects.filter(created_at__lt=cutoff)

        count = 0
        for task in old_tasks:
            self._delete_task_files(task)
            task.delete()
            count += 1

        logger.info(
            "Cleanup completed: deleted %d tasks older than %d hours",
            count,
            max_age,
        )
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} old tasks"))

    def _delete_task_files(self, task: Task):
        media_root = Path(settings.MEDIA_ROOT)
        for subdir in ("uploads", "stems"):
            task_dir = media_root / subdir / str(task.id)
            if task_dir.exists():
                shutil.rmtree(task_dir)
                logger.info("Deleted %s", task_dir)
