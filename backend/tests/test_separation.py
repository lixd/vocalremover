from unittest.mock import patch

import pytest

from separator.models import Task
from separator.separation import SeparationError, separate_audio


@pytest.mark.django_db
class TestSeparateAudio:
    @patch("separator.separation._run_spleeter")
    def test_2stems_separation(self, mock_spleeter, tmp_path):
        task = Task.objects.create(
            mode="2stems",
            original_filename="song.mp3",
            file_size=1024,
        )
        upload_dir = tmp_path / "uploads" / str(task.id)
        upload_dir.mkdir(parents=True)
        upload_file = upload_dir / "original.mp3"
        upload_file.write_bytes(b"fake audio")

        stem_dir = tmp_path / "stems" / str(task.id)
        stem_dir.mkdir(parents=True)
        (stem_dir / "vocals.wav").write_bytes(b"vocals data")
        (stem_dir / "accompaniment.wav").write_bytes(b"accompaniment data")

        mock_spleeter.return_value = {
            "vocals": str(stem_dir / "vocals.wav"),
            "accompaniment": str(stem_dir / "accompaniment.wav"),
        }

        result = separate_audio(task, media_root=tmp_path)
        assert "vocals" in result
        assert "accompaniment" in result
        mock_spleeter.assert_called_once()

    @patch("separator.separation._run_spleeter")
    def test_4stems_separation(self, mock_spleeter, tmp_path):
        task = Task.objects.create(
            mode="4stems",
            original_filename="song.wav",
            file_size=2048,
        )
        upload_dir = tmp_path / "uploads" / str(task.id)
        upload_dir.mkdir(parents=True)
        (upload_dir / "original.wav").write_bytes(b"fake audio")

        stem_dir = tmp_path / "stems" / str(task.id)
        stem_dir.mkdir(parents=True)
        for name in ("vocals", "drums", "bass", "other"):
            (stem_dir / f"{name}.wav").write_bytes(f"{name} data".encode())

        mock_spleeter.return_value = {
            name: str(stem_dir / f"{name}.wav")
            for name in ("vocals", "drums", "bass", "other")
        }

        result = separate_audio(task, media_root=tmp_path)
        assert len(result) == 4
        assert "drums" in result
        assert "bass" in result

    @patch("separator.separation._run_spleeter")
    def test_separation_failure_raises_error(self, mock_spleeter, tmp_path):
        task = Task.objects.create(
            mode="2stems",
            original_filename="corrupt.mp3",
            file_size=100,
        )
        upload_dir = tmp_path / "uploads" / str(task.id)
        upload_dir.mkdir(parents=True)
        (upload_dir / "original.mp3").write_bytes(b"corrupt")

        mock_spleeter.side_effect = RuntimeError("Spleeter inference failed")

        with pytest.raises(SeparationError, match="Spleeter inference failed"):
            separate_audio(task, media_root=tmp_path)

    @patch("separator.separation._run_spleeter")
    def test_missing_upload_file_raises_error(self, mock_spleeter, tmp_path):
        task = Task.objects.create(
            mode="2stems",
            original_filename="song.mp3",
            file_size=1024,
        )

        with pytest.raises(SeparationError, match="Upload file not found"):
            separate_audio(task, media_root=tmp_path)
