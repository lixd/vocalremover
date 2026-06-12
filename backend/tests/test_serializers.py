import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from separator.models import Task
from separator.serializers import TaskCreateSerializer, TaskSerializer


@pytest.mark.django_db
class TestTaskSerializer:
    def test_serialize_task(self, sample_task_data):
        task = Task.objects.create(**sample_task_data)
        serializer = TaskSerializer(task)
        data = serializer.data
        assert data["id"] == str(task.id)
        assert data["status"] == "PENDING"
        assert data["mode"] == "2stems"
        assert data["original_filename"] == "test.mp3"
        assert "created_at" in data
        assert "stems" in data

    def test_serialize_task_with_stems(self, sample_task_data):
        stems = {"vocals": "vocals.wav"}
        task = Task.objects.create(**sample_task_data, stems=stems)
        serializer = TaskSerializer(task)
        assert serializer.data["stems"] == stems


@pytest.mark.django_db
class TestTaskCreateSerializer:
    def test_valid_2stems_upload(self):
        audio = SimpleUploadedFile(
            "song.mp3", b"audio content", content_type="audio/mpeg"
        )
        serializer = TaskCreateSerializer(data={"file": audio, "mode": "2stems"})
        assert serializer.is_valid(), serializer.errors
        task = serializer.save()
        assert task.mode == "2stems"
        assert task.original_filename == "song.mp3"
        assert task.status == Task.Status.PENDING

    def test_valid_4stems_upload(self):
        audio = SimpleUploadedFile(
            "song.wav", b"audio content", content_type="audio/wav"
        )
        serializer = TaskCreateSerializer(data={"file": audio, "mode": "4stems"})
        assert serializer.is_valid(), serializer.errors
        task = serializer.save()
        assert task.mode == "4stems"

    def test_missing_mode(self):
        audio = SimpleUploadedFile(
            "song.mp3", b"audio content", content_type="audio/mpeg"
        )
        serializer = TaskCreateSerializer(data={"file": audio})
        assert not serializer.is_valid()
        assert "mode" in serializer.errors

    def test_invalid_mode(self):
        audio = SimpleUploadedFile(
            "song.mp3", b"audio content", content_type="audio/mpeg"
        )
        serializer = TaskCreateSerializer(data={"file": audio, "mode": "3stems"})
        assert not serializer.is_valid()
        assert "mode" in serializer.errors

    def test_unsupported_format(self):
        audio = SimpleUploadedFile(
            "song.txt", b"not audio", content_type="text/plain"
        )
        serializer = TaskCreateSerializer(data={"file": audio, "mode": "2stems"})
        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_file_too_large(self):
        large_content = b"x" * (20 * 1024 * 1024 + 1)
        audio = SimpleUploadedFile(
            "song.mp3", large_content, content_type="audio/mpeg"
        )
        serializer = TaskCreateSerializer(data={"file": audio, "mode": "2stems"})
        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_supported_formats(self):
        for ext, content_type in [
            ("mp3", "audio/mpeg"),
            ("wav", "audio/wav"),
            ("flac", "audio/flac"),
            ("ogg", "audio/ogg"),
            ("m4a", "audio/mp4"),
        ]:
            audio = SimpleUploadedFile(
                f"song.{ext}", b"audio content", content_type=content_type
            )
            serializer = TaskCreateSerializer(
                data={"file": audio, "mode": "2stems"}
            )
            assert serializer.is_valid(), (
                f"{ext} should be valid: {serializer.errors}"
            )

    def test_missing_file(self):
        serializer = TaskCreateSerializer(data={"mode": "2stems"})
        assert not serializer.is_valid()
        assert "file" in serializer.errors
