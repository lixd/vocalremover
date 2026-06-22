import io
import uuid
import zipfile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APIClient

from separator.models import Task


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_task(db):
    def _create(status=Task.Status.PENDING, mode="2stems", stems=None):
        return Task.objects.create(
            status=status,
            mode=mode,
            original_filename="test.mp3",
            file_size=1024,
            stems=stems or {},
        )
    return _create


@pytest.mark.django_db
class TestCreateTaskEndpoint:
    def test_create_task_success(self, api_client):
        audio = SimpleUploadedFile("song.mp3", b"audio content", content_type="audio/mpeg")
        response = api_client.post(
            "/api/tasks/", {"file": audio, "mode": "2stems"}, format="multipart"
        )
        assert response.status_code == 201
        assert "id" in response.data
        assert response.data["status"] == "PENDING"
        assert response.data["mode"] == "2stems"
        assert response.data["original_filename"] == "song.mp3"

    def test_create_task_missing_file(self, api_client):
        response = api_client.post("/api/tasks/", {"mode": "2stems"}, format="multipart")
        assert response.status_code == 400
        assert "file" in response.data

    def test_create_task_missing_mode(self, api_client):
        audio = SimpleUploadedFile("song.mp3", b"audio content", content_type="audio/mpeg")
        response = api_client.post("/api/tasks/", {"file": audio}, format="multipart")
        assert response.status_code == 400
        assert "mode" in response.data

    def test_create_task_unsupported_format(self, api_client):
        audio = SimpleUploadedFile("song.txt", b"not audio", content_type="text/plain")
        response = api_client.post(
            "/api/tasks/", {"file": audio, "mode": "2stems"}, format="multipart"
        )
        assert response.status_code == 400
        assert "file" in response.data

    def test_create_task_file_too_large(self, api_client):
        large_content = b"x" * (20 * 1024 * 1024 + 1)
        audio = SimpleUploadedFile("song.mp3", large_content, content_type="audio/mpeg")
        response = api_client.post(
            "/api/tasks/", {"file": audio, "mode": "2stems"}, format="multipart"
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestGetTaskEndpoint:
    def test_get_task_success(self, api_client, create_task):
        task = create_task()
        response = api_client.get(f"/api/tasks/{task.id}/")
        assert response.status_code == 200
        assert response.data["id"] == str(task.id)
        assert response.data["status"] == "PENDING"

    def test_get_task_not_found(self, api_client):
        fake_id = uuid.uuid4()
        response = api_client.get(f"/api/tasks/{fake_id}/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestStemsEndpoint:
    def test_list_stems_completed(self, api_client, create_task):
        stems = {
            "vocals": {"filename": "vocals.wav", "size": 1024},
            "accompaniment": {"filename": "accompaniment.wav", "size": 2048},
        }
        task = create_task(status=Task.Status.COMPLETED, stems=stems)
        response = api_client.get(f"/api/tasks/{task.id}/stems/")
        assert response.status_code == 200
        assert "vocals" in response.data
        assert "accompaniment" in response.data

    def test_list_stems_not_completed(self, api_client, create_task):
        task = create_task(status=Task.Status.PROCESSING)
        response = api_client.get(f"/api/tasks/{task.id}/stems/")
        assert response.status_code == 200
        assert response.data == {}

    def test_stem_download_success(self, api_client, create_task, tmp_path):
        stems = {"vocals": {"filename": "vocals.wav"}}
        task = create_task(status=Task.Status.COMPLETED, stems=stems)
        stem_dir = tmp_path / "stems" / str(task.id)
        stem_dir.mkdir(parents=True)
        (stem_dir / "vocals.wav").write_bytes(b"fake wav data")

        with override_settings(MEDIA_ROOT=tmp_path):
            response = api_client.get(f"/api/tasks/{task.id}/stems/vocals/")
        assert response.status_code == 200
        assert response["Content-Disposition"].startswith("attachment")
        # 文件名带源文件名前缀 + 中文标签（test.mp3 → test-人声.wav）
        assert "filename*=UTF-8''test-%E4%BA%BA%E5%A3%B0.wav" in response["Content-Disposition"]

    def test_stem_download_not_found(self, api_client, create_task, tmp_path):
        stems = {"vocals": {"filename": "vocals.wav"}}
        task = create_task(status=Task.Status.COMPLETED, stems=stems)

        with override_settings(MEDIA_ROOT=tmp_path):
            response = api_client.get(f"/api/tasks/{task.id}/stems/vocals/")
        assert response.status_code == 404

    def test_stem_download_invalid_name(self, api_client, create_task, tmp_path):
        stems = {"vocals": {"filename": "vocals.wav"}}
        task = create_task(status=Task.Status.COMPLETED, stems=stems)

        with override_settings(MEDIA_ROOT=tmp_path):
            response = api_client.get(f"/api/tasks/{task.id}/stems/../../etc/passwd/")
        assert response.status_code in (400, 404)

    def test_stem_stream_success(self, api_client, create_task, tmp_path):
        stems = {"vocals": {"filename": "vocals.wav"}}
        task = create_task(status=Task.Status.COMPLETED, stems=stems)
        stem_dir = tmp_path / "stems" / str(task.id)
        stem_dir.mkdir(parents=True)
        (stem_dir / "vocals.wav").write_bytes(b"fake wav data" * 100)

        with override_settings(MEDIA_ROOT=tmp_path):
            response = api_client.get(f"/api/tasks/{task.id}/stems/vocals/stream/")
        assert response.status_code == 200
        assert response.get("Accept-Ranges") == "bytes"
        assert response["Content-Type"] == "audio/wav"

    def test_download_all_stems(self, api_client, create_task, tmp_path):
        stems = {
            "vocals": {"filename": "vocals.wav"},
            "accompaniment": {"filename": "accompaniment.wav"},
        }
        task = create_task(status=Task.Status.COMPLETED, stems=stems)
        stem_dir = tmp_path / "stems" / str(task.id)
        stem_dir.mkdir(parents=True)
        (stem_dir / "vocals.wav").write_bytes(b"vocals data")
        (stem_dir / "accompaniment.wav").write_bytes(b"accompaniment data")

        with override_settings(MEDIA_ROOT=tmp_path):
            response = api_client.get(f"/api/tasks/{task.id}/stems/download-all/")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/zip"
        # ZIP 名带源文件名前缀 + UTF-8 编码（test.mp3 → test-stems.zip）
        assert "filename*=UTF-8''test-stems.zip" in response["Content-Disposition"]
        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer) as zf:
            names = zf.namelist()
            assert "test-人声.wav" in names
            assert "test-伴奏.wav" in names
