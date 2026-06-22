import io
import logging
import zipfile
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from separator.models import Task
from separator.serializers import TaskCreateSerializer, TaskSerializer

logger = logging.getLogger(__name__)

ALLOWED_STEM_NAMES = {
    "vocals",
    "accompaniment",
    "drums",
    "bass",
    "other",
}

# stem 名称 → 中文标签，用于下载文件名
STEM_LABELS = {
    "vocals": "人声",
    "accompaniment": "伴奏",
    "drums": "鼓",
    "bass": "贝斯",
    "other": "其他",
}


def _build_content_disposition(filename: str) -> str:
    """Build a Content-Disposition header that handles non-ASCII filenames.

    Uses RFC 5987 ``filename*`` so Chinese characters survive across browsers;
    falls back to an ASCII-only ``filename`` for older clients.
    """
    quoted = quote(filename)
    ascii_fallback = filename.encode("ascii", "ignore").decode("ascii") or "download"
    return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{quoted}"


def _stem_download_name(task: Task, stem_name: str, ext: str) -> str:
    """Build a stem download filename like ``a-人声.mp3`` from the source name."""
    source_stem = Path(task.original_filename).stem or "audio"
    label = STEM_LABELS.get(stem_name, stem_name)
    return f"{source_stem}-{label}{ext}"



@api_view(["POST"])
def create_task(request):
    serializer = TaskCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    task = serializer.save()
    return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def get_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response(
            {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
        )
    return Response(TaskSerializer(task).data)


@api_view(["GET"])
def list_stems(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response(
            {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
        )
    return Response(task.stems)


def _find_stem_file(task_id: str, stem_name: str) -> Path | None:
    """Find stem file, checking both .mp3 and .wav extensions."""
    stem_dir = Path(settings.MEDIA_ROOT) / "stems" / task_id
    for ext in (".mp3", ".wav"):
        path = stem_dir / f"{stem_name}{ext}"
        if path.exists():
            return path
    return None


@csrf_exempt
@require_GET
def stem_download(request, task_id, stem_name):
    """Download a stem file (plain Django view, no DRF content negotiation)."""
    if stem_name not in ALLOWED_STEM_NAMES:
        return JsonResponse({"error": "Invalid stem name"}, status=400)

    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)

    stem_path = _find_stem_file(str(task_id), stem_name)
    if stem_path is None:
        return JsonResponse({"error": "Stem not found"}, status=404)

    content_type = "audio/mpeg" if stem_path.suffix == ".mp3" else "audio/wav"
    filename = _stem_download_name(task, stem_name, stem_path.suffix)
    response = FileResponse(open(stem_path, "rb"), content_type=content_type)
    response["Content-Disposition"] = _build_content_disposition(filename)
    return response


@csrf_exempt
@require_GET
def stem_stream(request, task_id, stem_name):
    """Stream a stem file for playback (plain Django view with Range support).

    wavesurfer.js and HTML5 <audio> both use fetch() which interacts poorly
    with DRF's content negotiation. This view bypasses DRF entirely.
    """
    if stem_name not in ALLOWED_STEM_NAMES:
        return JsonResponse({"error": "Invalid stem name"}, status=400)

    stem_path = _find_stem_file(str(task_id), stem_name)
    if stem_path is None:
        return JsonResponse({"error": "Stem not found"}, status=404)

    file_size = stem_path.stat().st_size
    content_type = "audio/mpeg" if stem_path.suffix == ".mp3" else "audio/wav"

    # Handle Range requests for seeking
    range_header = request.META.get("HTTP_RANGE")
    if range_header:
        try:
            range_spec = range_header.replace("bytes=", "").strip()
            start_str, end_str = range_spec.split("-")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
            end = min(end, file_size - 1)
            length = end - start + 1

            with open(stem_path, "rb") as fh:
                fh.seek(start)
                data = fh.read(length)
            response = HttpResponse(
                data, status=206, content_type=content_type
            )
            response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            response["Content-Length"] = str(length)
            response["Accept-Ranges"] = "bytes"
            response["Access-Control-Allow-Origin"] = "*"
            return response
        except (ValueError, OSError):
            pass

    response = FileResponse(open(stem_path, "rb"), content_type=content_type)
    response["Content-Length"] = str(file_size)
    response["Accept-Ranges"] = "bytes"
    response["Access-Control-Allow-Origin"] = "*"
    return response


@csrf_exempt
@require_GET
def download_all_stems(request, task_id):
    """Download all stems as a ZIP archive."""
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)

    stem_dir = Path(settings.MEDIA_ROOT) / "stems" / str(task_id)
    if not stem_dir.exists():
        return JsonResponse({"error": "Stems not found"}, status=404)

    source_stem = Path(task.original_filename).stem or "audio"

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for stem_file in list(stem_dir.glob("*.mp3")) + list(stem_dir.glob("*.wav")):
            stem_name = stem_file.stem
            label = STEM_LABELS.get(stem_name, stem_name)
            arcname = f"{source_stem}-{label}{stem_file.suffix}"
            zf.write(stem_file, arcname)
    buffer.seek(0)

    zip_name = f"{source_stem}-stems.zip"
    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = _build_content_disposition(zip_name)
    return response
