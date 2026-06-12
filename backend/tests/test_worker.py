import signal
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from django.utils import timezone

from separator.models import Task
from separator.worker import Worker


@pytest.fixture
def worker(tmp_path):
    return Worker(media_root=tmp_path, poll_interval=0.01)


@pytest.mark.django_db
class TestWorker:
    def test_process_pending_task_success(self, worker, tmp_path):
        task = Task.objects.create(
            mode="2stems",
            original_filename="song.mp3",
            file_size=1024,
        )
        assert task.status == Task.Status.PENDING

        with patch("separator.worker.separate_audio") as mock_sep:
            mock_sep.return_value = {
                "vocals": str(tmp_path / "stems" / str(task.id) / "vocals.wav"),
                "accompaniment": str(
                    tmp_path / "stems" / str(task.id) / "accompaniment.wav"
                ),
            }
            worker._process_task(task)

        task.refresh_from_db()
        assert task.status == Task.Status.COMPLETED
        assert task.completed_at is not None
        assert "vocals" in task.stems
        assert "accompaniment" in task.stems

    def test_process_task_failure(self, worker, tmp_path):
        task = Task.objects.create(
            mode="2stems",
            original_filename="corrupt.mp3",
            file_size=100,
        )

        with patch("separator.worker.separate_audio") as mock_sep:
            mock_sep.side_effect = RuntimeError("Spleeter crashed")
            worker._process_task(task)

        task.refresh_from_db()
        assert task.status == Task.Status.FAILED
        assert task.error_message == "Spleeter crashed"
        assert task.completed_at is None

    def test_recover_stuck_processing_tasks(self, worker):
        stuck_task = Task.objects.create(
            mode="2stems",
            original_filename="stuck.mp3",
            file_size=512,
            status=Task.Status.PROCESSING,
        )
        Task.objects.filter(id=stuck_task.id).update(
            updated_at=timezone.now() - timedelta(minutes=31)
        )

        worker._recover_stuck_tasks()
        stuck_task.refresh_from_db()
        assert stuck_task.status == Task.Status.FAILED
        assert "timeout" in stuck_task.error_message.lower()

    def test_recover_ignores_recent_processing_tasks(self, worker):
        recent_task = Task.objects.create(
            mode="2stems",
            original_filename="recent.mp3",
            file_size=512,
            status=Task.Status.PROCESSING,
        )

        worker._recover_stuck_tasks()
        recent_task.refresh_from_db()
        assert recent_task.status == Task.Status.PROCESSING

    def test_graceful_shutdown(self, worker):
        worker._shutdown = False
        worker._handle_shutdown(signal.SIGTERM, None)
        assert worker._shutdown is True
