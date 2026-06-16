import io
import logging
import zipfile
from pathlib import Path

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

    stem_path = _find_stem_file(str(task_id), stem_name)
    if stem_path is None:
        return JsonResponse({"error": "Stem not found"}, status=404)

    content_type = "audio/mpeg" if stem_path.suffix == ".mp3" else "audio/wav"
    response = FileResponse(open(stem_path, "rb"), content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{stem_name}{stem_path.suffix}"'
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
    stem_dir = Path(settings.MEDIA_ROOT) / "stems" / str(task_id)
    if not stem_dir.exists():
        return JsonResponse({"error": "Stems not found"}, status=404)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for stem_file in list(stem_dir.glob("*.mp3")) + list(stem_dir.glob("*.wav")):
            zf.write(stem_file, stem_file.name)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{task_id}_stems.zip"'
    return response
