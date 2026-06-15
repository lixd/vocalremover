import logging
import signal
import time
from datetime import timedelta
from pathlib import Path

from django.db import transaction
from django.utils import timezone

from separator.models import Task
from separator.separation import separate_audio

logger = logging.getLogger(__name__)

STUCK_TIMEOUT_MINUTES = 30


class Worker:
    def __init__(self, media_root: Path | None = None, poll_interval: float = 2.0):
        self._shutdown = False
        self._media_root = media_root
        self._poll_interval = poll_interval

    def _handle_shutdown(self, signum, frame):
        logger.info("Received signal %s, shutting down gracefully...", signum)
        self._shutdown = True

    def _recover_stuck_tasks(self):
        cutoff = timezone.now() - timedelta(minutes=STUCK_TIMEOUT_MINUTES)
        stuck_tasks = Task.objects.filter(
            status=Task.Status.PROCESSING, updated_at__lt=cutoff
        )
        count = stuck_tasks.update(
            status=Task.Status.FAILED,
            error_message="Task timeout: no heartbeat for over 30 minutes",
        )
        if count > 0:
            logger.warning("Recovered %d stuck PROCESSING tasks", count)

    def _process_task(self, task: Task):
        task.status = Task.Status.PROCESSING
        task.save(update_fields=["status", "updated_at"])
        logger.info("Processing task %s", task.id)

        try:
            stems = separate_audio(task, media_root=self._media_root)
            task.stems = stems
            task.status = Task.Status.COMPLETED
            task.completed_at = timezone.now()
            task.save()
            logger.info("Task %s completed with stems: %s", task.id, list(stems.keys()))
        except Exception as exc:
            task.status = Task.Status.FAILED
            task.error_message = str(exc)
            task.save(update_fields=["status", "error_message", "updated_at"])
            logger.error("Task %s failed: %s", task.id, exc)

    def _claim_pending_task(self) -> Task | None:
        with transaction.atomic():
            task = (
                Task.objects.select_for_update(skip_locked=True)
                .filter(status=Task.Status.PENDING)
                .order_by("created_at")
                .first()
            )
        return task

    def run(self):
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        # Pre-load Spleeter models at startup
        from separator.separation import _get_separator, SPLEETER_MODE_MAP

        logger.info("Pre-loading Spleeter models...")
        for preset in SPLEETER_MODE_MAP.values():
            _get_separator(preset)
        logger.info("All models loaded")

        logger.info("Worker started (poll_interval=%.1fs)", self._poll_interval)
        self._recover_stuck_tasks()

        while not self._shutdown:
            try:
                task = self._claim_pending_task()
                if task:
                    self._process_task(task)
                else:
                    time.sleep(self._poll_interval)
            except Exception:
                logger.exception("Unexpected error in worker loop")
                time.sleep(self._poll_interval)

        logger.info("Worker stopped")
