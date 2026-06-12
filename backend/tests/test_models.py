import pytest
from django.utils import timezone

from separator.models import Task


@pytest.mark.django_db
class TestTaskModel:
    def test_create_task_with_defaults(self, sample_task_data):
        task = Task.objects.create(**sample_task_data)
        assert task.status == Task.Status.PENDING
        assert task.mode == "2stems"
        assert task.original_filename == "test.mp3"
        assert task.id is not None
        assert task.created_at is not None
        assert task.updated_at is not None
        assert task.completed_at is None
        assert task.error_message is None
        assert task.stems == {}

    def test_task_has_uuid_primary_key(self, sample_task_data):
        task = Task.objects.create(**sample_task_data)
        assert len(str(task.id)) == 36

    def test_status_transitions(self, sample_task_data):
        task = Task.objects.create(**sample_task_data)
        assert task.status == Task.Status.PENDING

        task.status = Task.Status.PROCESSING
        task.save()
        task.refresh_from_db()
        assert task.status == Task.Status.PROCESSING

        task.status = Task.Status.COMPLETED
        task.completed_at = timezone.now()
        task.save()
        task.refresh_from_db()
        assert task.status == Task.Status.COMPLETED
        assert task.completed_at is not None

    def test_failed_status_with_error_message(self, sample_task_data):
        task = Task.objects.create(**sample_task_data)
        task.status = Task.Status.FAILED
        task.error_message = "Spleeter inference failed"
        task.save()
        task.refresh_from_db()
        assert task.status == Task.Status.FAILED
        assert task.error_message == "Spleeter inference failed"

    def test_stems_json_field(self, sample_task_data):
        stems = {"vocals": "/media/stems/abc/vocals.wav"}
        task = Task.objects.create(**sample_task_data, stems=stems)
        task.refresh_from_db()
        assert task.stems == stems

    def test_mode_choices(self, sample_task_data):
        task_2 = Task.objects.create(**{**sample_task_data, "mode": "2stems"})
        task_4 = Task.objects.create(**{**sample_task_data, "mode": "4stems"})
        assert task_2.mode == "2stems"
        assert task_4.mode == "4stems"
