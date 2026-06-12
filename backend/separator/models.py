from uuid import uuid4

from django.db import models


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        PROCESSING = "PROCESSING"
        COMPLETED = "COMPLETED"
        FAILED = "FAILED"

    class Mode(models.TextChoices):
        TWO_STEMS = "2stems"
        FOUR_STEMS = "4stems"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    mode = models.CharField(max_length=16, choices=Mode.choices)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    stems = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Task({self.id}, {self.status}, {self.mode})"
