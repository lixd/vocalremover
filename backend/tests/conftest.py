import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.fixture
def sample_audio_file():
    return SimpleUploadedFile(
        "test.mp3",
        b"fake audio content for testing",
        content_type="audio/mpeg",
    )


@pytest.fixture
def sample_task_data(sample_audio_file):
    return {
        "mode": "2stems",
        "original_filename": "test.mp3",
        "file_size": sample_audio_file.size,
    }
