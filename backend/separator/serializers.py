from pathlib import Path

from django.core.files.storage import default_storage
from rest_framework import serializers

from separator.models import Task

ALLOWED_EXTENSIONS: set[str] = {"mp3", "wav", "flac", "ogg", "m4a"}
MAX_FILE_SIZE: int = 20 * 1024 * 1024  # 20MB


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "status",
            "mode",
            "original_filename",
            "file_size",
            "created_at",
            "updated_at",
            "completed_at",
            "error_message",
            "stems",
        ]
        read_only_fields = fields


class TaskCreateSerializer(serializers.Serializer):
    file = serializers.FileField()
    mode = serializers.ChoiceField(choices=Task.Mode.choices)

    def validate_file(self, value):
        extension = value.name.rsplit(".", 1)[-1].lower() if "." in value.name else ""
        if extension not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported format. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )
        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError("File too large. Max size: 20MB")
        return value

    def create(self, validated_data):
        uploaded_file = validated_data["file"]
        task = Task.objects.create(
            mode=validated_data["mode"],
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
        )
        ext = Path(uploaded_file.name).suffix
        upload_path = f"uploads/{task.id}/original{ext}"
        default_storage.save(upload_path, uploaded_file)
        return task
