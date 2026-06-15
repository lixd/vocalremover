import logging
import shutil
import subprocess
from pathlib import Path

from separator.models import Task

logger = logging.getLogger(__name__)

# Only use 4stems model — 2stems is derived by merging drums+bass+other into accompaniment
SPLEETER_PRESET = "spleeter:4stems"

STEM_NAMES = {
    Task.Mode.TWO_STEMS: ["vocals", "accompaniment"],
    Task.Mode.FOUR_STEMS: ["vocals", "drums", "bass", "other"],
}

# Components that make up "accompaniment" when using 4stems for 2stems mode
ACCOMPANIMENT_STEMS = ["drums", "bass", "other"]

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


def _merge_to_mp3(wav_files: list[Path], output_path: Path) -> None:
    """Merge multiple WAV files into a single MP3 using ffmpeg."""
    if len(wav_files) == 1:
        # Single file, just convert
        subprocess.run(
            ["ffmpeg", "-i", str(wav_files[0]), "-codec:a", "libmp3lame", "-qscale:a", "2", "-y", str(output_path)],
            check=True, capture_output=True, timeout=60,
        )
    else:
        # Merge multiple WAVs: concat demuxer requires same format, so use filter_complex
        inputs = []
        filter_parts = []
        for i, wav in enumerate(wav_files):
            inputs.extend(["-i", str(wav)])
            filter_parts.append(f"[{i}:a]")
        filter_str = "".join(filter_parts) + f"amix=inputs={len(wav_files)}:duration=longest[a]"
        subprocess.run(
            ["ffmpeg", *inputs, "-filter_complex", filter_str, "-map", "[a]",
             "-codec:a", "libmp3lame", "-qscale:a", "2", "-y", str(output_path)],
            check=True, capture_output=True, timeout=60,
        )


def separate_audio(
    task: Task, media_root: Path | None = None
) -> dict[str, str]:
    """Invoke Spleeter to separate an audio file.

    Always uses the 4stems model. For 2stems mode, merges drums+bass+other
    into a single accompaniment track.

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
    stem_names = STEM_NAMES[task.mode]

    logger.info(
        "Starting separation for task %s (mode=%s)", task.id, task.mode
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

    if task.mode == Task.Mode.TWO_STEMS:
        # 2stems mode: vocals as-is, merge drums+bass+other into accompaniment
        vocals_wav = spleeter_subdir / "vocals.wav"
        if vocals_wav.exists():
            mp3_dst = task_stem_dir / "vocals.mp3"
            try:
                subprocess.run(
                    ["ffmpeg", "-i", str(vocals_wav), "-codec:a", "libmp3lame", "-qscale:a", "2", "-y", str(mp3_dst)],
                    check=True, capture_output=True, timeout=60,
                )
                result["vocals"] = str(mp3_dst)
                logger.info("Converted vocals to MP3")
            except (subprocess.CalledProcessError, FileNotFoundError) as exc:
                wav_dst = task_stem_dir / "vocals.wav"
                vocals_wav.rename(wav_dst)
                result["vocals"] = str(wav_dst)
                logger.warning("ffmpeg conversion failed for vocals, keeping WAV: %s", exc)

        # Merge accompaniment components
        accomp_wavs = [spleeter_subdir / f"{name}.wav" for name in ACCOMPANIMENT_STEMS]
        accomp_wavs = [w for w in accomp_wavs if w.exists()]
        if accomp_wavs:
            mp3_dst = task_stem_dir / "accompaniment.mp3"
            try:
                _merge_to_mp3(accomp_wavs, mp3_dst)
                result["accompaniment"] = str(mp3_dst)
                logger.info("Merged and converted accompaniment to MP3")
            except (subprocess.CalledProcessError, FileNotFoundError) as exc:
                # Fallback: just keep drums as accompaniment
                wav_dst = task_stem_dir / "accompaniment.wav"
                accomp_wavs[0].rename(wav_dst)
                result["accompaniment"] = str(wav_dst)
                logger.warning("Accompaniment merge failed, keeping first component: %s", exc)
    else:
        # 4stems mode: each stem as-is
        for name in stem_names:
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
