import logging
import shutil
import subprocess
from pathlib import Path

from separator.models import Task

logger = logging.getLogger(__name__)

SPLEETER_MODE_MAP = {
    Task.Mode.TWO_STEMS: "spleeter:2stems",
    Task.Mode.FOUR_STEMS: "spleeter:4stems",
}

STEM_NAMES = {
    Task.Mode.TWO_STEMS: ["vocals", "accompaniment"],
    Task.Mode.FOUR_STEMS: ["vocals", "drums", "bass", "other"],
}


class SeparationError(Exception):
    """Raised when Spleeter fails to separate audio."""


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


def _run_spleeter(
    input_path: str, output_dir: str, preset: str, stem_names: list[str]
) -> dict[str, str]:
    """Call Spleeter's Python API to separate audio.

    Returns dict mapping stem names to output file paths.
    """
    from spleeter.separator import Separator

    separator = Separator(preset)
    separator.separate_to_file(input_path, output_dir)

    input_stem = Path(input_path).stem

    result = {}
    for name in stem_names:
        stem_path = Path(output_dir) / input_stem / f"{name}.wav"
        if stem_path.exists():
            result[name] = str(stem_path)
    return result


def separate_audio(
    task: Task, media_root: Path | None = None
) -> dict[str, str]:
    """Invoke Spleeter to separate an audio file.

    Args:
        task: Task instance with mode and uploaded file path.
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
    preset = SPLEETER_MODE_MAP[task.mode]
    stem_names = STEM_NAMES[task.mode]

    logger.info(
        "Starting separation for task %s (mode=%s)", task.id, task.mode
    )

    try:
        raw_result = _run_spleeter(str(upload_file), output_dir, preset, stem_names)
    except Exception as exc:
        logger.error("Spleeter failed for task %s: %s", task.id, exc)
        raise SeparationError(str(exc)) from exc

    # Spleeter outputs to stems/{filename_stem}/ — move to stems/{task_id}/
    task_stem_dir = media_root / "stems" / str(task.id)
    task_stem_dir.mkdir(parents=True, exist_ok=True)

    result = {}
    for name, src_path in raw_result.items():
        src = Path(src_path)
        if src.exists():
            # Convert WAV to MP3 to reduce file size
            mp3_dst = task_stem_dir / f"{name}.mp3"
            try:
                subprocess.run(
                    ["ffmpeg", "-i", str(src), "-codec:a", "libmp3lame", "-qscale:a", "2", "-y", str(mp3_dst)],
                    check=True, capture_output=True, timeout=60,
                )
                src.unlink(missing_ok=True)
                result[name] = str(mp3_dst)
                logger.info("Converted %s to MP3: %s → %s", name, src.name, mp3_dst.name)
            except (subprocess.CalledProcessError, FileNotFoundError) as exc:
                # ffmpeg not available or failed — keep WAV
                wav_dst = task_stem_dir / f"{name}.wav"
                src.rename(wav_dst)
                result[name] = str(wav_dst)
                logger.warning("ffmpeg conversion failed for %s, keeping WAV: %s", name, exc)

    # Cleanup Spleeter's original subdirectory
    spleeter_subdir = Path(output_dir) / Path(upload_file).stem
    if spleeter_subdir.exists() and spleeter_subdir != task_stem_dir:
        shutil.rmtree(spleeter_subdir, ignore_errors=True)

    logger.info(
        "Separation completed for task %s: %s", task.id, list(result.keys())
    )
    return result
