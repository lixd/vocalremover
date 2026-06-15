import logging
import shutil
import subprocess
from pathlib import Path

from separator.models import Task

logger = logging.getLogger(__name__)

SPLEETER_PRESET = "spleeter:2stems"

# Cached Separator instance — load model once, reuse across tasks
_separator = None


def _get_separator():
    """Get or create the cached Separator."""
    global _separator
    if _separator is None:
        from spleeter.separator import Separator

        logger.info("Loading Spleeter model: %s", SPLEETER_PRESET)
        _separator = Separator(SPLEETER_PRESET)
        logger.info("Model loaded: %s", SPLEETER_PRESET)
    return _separator


def _find_upload_file(task_id: str, media_root: Path) -> Path:
    """Locate the uploaded file for a given task.

    Raises SeparationError if the upload directory is missing or empty.
    """
    upload_dir = media_root / "uploads" / task_id
    if not upload_dir.exists():
        raise SeparationError(f"Upload file not found for task {task_id}")
    files = list(upload_dir.iterdir())
    if not files:
        raise SeparationError(f"Upload file not found for task {task_id}")
    return files[0]


def separate_audio(
    task: Task, media_root: Path | None = None
) -> dict[str, str]:
    """Invoke Spleeter to separate an audio file into vocals and accompaniment.

    Args:
        task: Task instance with uploaded file path.
        media_root: Override MEDIA_ROOT for testing.

    Returns:
        Dict mapping stem names to file paths.

    Raises:
        SeparationError: If Spleeter inference fails.
    """
    if media_root is None:
        from django.conf import settings

        media_root = Path(settings.MEDIA_ROOT)

    upload_file = _find_upload_file(str(task.id), media_root)
    output_dir = str(media_root / "stems")

    logger.info(
        "Starting separation for task %s", task.id
    )

    try:
        separator = _get_separator()
        separator.separate_to_file(str(upload_file), output_dir)
    except Exception as exc:
        logger.error("Spleeter failed for task %s: %s", task.id, exc)
        raise SeparationError(str(exc)) from exc

    # Spleeter outputs to stems/{filename_stem}/ — move to stems/{task_id}/
    input_stem = Path(upload_file).stem
    spleeter_subdir = Path(output_dir) / input_stem
    task_stem_dir = media_root / "stems" / str(task.id)
    task_stem_dir.mkdir(parents=True, exist_ok=True)

    result = {}
    for name in ["vocals", "accompaniment"]:
        wav_path = spleeter_subdir / f"{name}.wav"
        if wav_path.exists():
            mp3_dst = task_stem_dir / f"{name}.mp3"
            try:
                subprocess.run(
                    ["ffmpeg", "-i", str(wav_path), "-codec:a", "libmp3lame", "-qscale:a", "2", "-y", str(mp3_dst)],
                    check=True, capture_output=True, timeout=60,
                )
                result[name] = str(mp3_dst)
                logger.info("Converted %s to MP3", name)
            except (subprocess.CalledProcessError, FileNotFoundError) as exc:
                wav_dst = task_stem_dir / f"{name}.wav"
                wav_path.rename(wav_dst)
                result[name] = str(wav_dst)
                logger.warning("ffmpeg conversion failed for %s, keeping WAV: %s", name, exc)

    # Cleanup Spleeter's original subdirectory
    if spleeter_subdir.exists() and spleeter_subdir != task_stem_dir:
        shutil.rmtree(spleeter_subdir, ignore_errors=True)

    logger.info(
        "Separation completed for task %s: %s", task.id, list(result.keys())
    )
    return result
