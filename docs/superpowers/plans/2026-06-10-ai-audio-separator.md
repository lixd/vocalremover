---
change: ai-audio-separator
design-doc: docs/superpowers/specs/2026-06-10-ai-audio-separator-design.md
base-ref: 9b048dcb12dbb636821422f20cf0d486e58ff2e4
---

# AI Audio Separator 实现计划

> **致自动化工作器：** 必须使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务执行本计划。步骤使用 checkbox (`- [ ]`) 进行跟踪。

**目标：** 构建一个 Web 应用，用户上传音频文件后，使用 Spleeter 将其分离为人声、鼓、贝斯、其他音轨，并提供波形预览、播放和下载功能。

**架构：** Django + DRF 后端处理文件上传和任务管理，Vue 3 + TypeScript 前端提供交互界面，Worker 管理命令轮询待处理任务并调用 Spleeter 进行音频分离，SQLite 作为数据库，本地文件系统存储音频文件。

**技术栈：** Python 3.11+, Django 5.x, DRF 3.x, Spleeter 2.4, Vue 3, Vite 6.x, TypeScript 5.x, Element Plus, wavesurfer.js 7.x, axios, uv

---

## 文件结构总览

### 后端文件

| 文件 | 职责 |
|------|------|
| `backend/pyproject.toml` | Python 依赖和项目元数据 |
| `backend/manage.py` | Django 管理入口 |
| `backend/config/__init__.py` | Django 项目包 |
| `backend/config/settings.py` | Django 配置（数据库、CORS、媒体路径、已安装应用） |
| `backend/config/urls.py` | 根 URL 配置 |
| `backend/config/wsgi.py` | WSGI 入口 |
| `backend/separator/__init__.py` | 核心应用包 |
| `backend/separator/models.py` | Task 模型定义 |
| `backend/separator/serializers.py` | DRF 序列化器 |
| `backend/separator/views.py` | API 视图（创建任务、查询状态、下载/流式传输） |
| `backend/separator/urls.py` | 应用级 URL 路由 |
| `backend/separator/admin.py` | Django Admin 自定义配置 |
| `backend/separator/separation.py` | Spleeter 封装（调用 Python API） |
| `backend/separator/worker.py` | Worker 轮询逻辑（状态机、错误处理、信号处理） |
| `backend/separator/management/commands/run_worker.py` | Worker 管理命令入口 |
| `backend/separator/management/commands/cleanup_old_tasks.py` | 清理旧任务管理命令 |
| `backend/tests/conftest.py` | pytest 公共 fixtures |
| `backend/tests/test_models.py` | 模型单元测试 |
| `backend/tests/test_serializers.py` | 序列化器单元测试 |
| `backend/tests/test_views.py` | API 端点集成测试 |
| `backend/tests/test_separation.py` | Spleeter 封装单元测试 |
| `backend/tests/test_worker.py` | Worker 逻辑单元测试 |

### 前端文件

| 文件 | 职责 |
|------|------|
| `frontend/package.json` | npm 依赖和脚本 |
| `frontend/tsconfig.json` | TypeScript 配置 |
| `frontend/vite.config.ts` | Vite 配置（代理、构建） |
| `frontend/index.html` | HTML 入口 |
| `frontend/src/main.ts` | Vue 应用入口 |
| `frontend/src/App.vue` | 根组件（RouterView） |
| `frontend/src/router/index.ts` | Vue Router 配置 |
| `frontend/src/types/index.ts` | TypeScript 接口定义 |
| `frontend/src/api/client.ts` | Axios 实例 + API 函数 |
| `frontend/src/composables/useTask.ts` | 任务轮询 composable |
| `frontend/src/composables/useAudioPlayer.ts` | 音频播放 composable |
| `frontend/src/components/FileUploader.vue` | 文件上传组件（拖拽 + 点击） |
| `frontend/src/components/ModeSelector.vue` | 分离模式选择组件 |
| `frontend/src/components/TaskProgress.vue` | 任务进度显示组件 |
| `frontend/src/components/StemPlayer.vue` | 音轨波形播放组件 |
| `frontend/src/components/DownloadPanel.vue` | 下载面板组件 |
| `frontend/src/views/HomeView.vue` | 首页视图（上传 + 模式选择） |
| `frontend/src/views/ResultView.vue` | 结果页视图（进度 + 音轨播放） |
| `frontend/src/__tests__/api-client.test.ts` | API 客户端测试 |
| `frontend/src/__tests__/FileUploader.test.ts` | FileUploader 组件测试 |
| `frontend/src/__tests__/ModeSelector.test.ts` | ModeSelector 组件测试 |
| `frontend/src/__tests__/TaskProgress.test.ts` | TaskProgress 组件测试 |

---

## Task 1: 初始化 Django 项目

**文件：**
- Create: `backend/pyproject.toml`
- Create: `backend/manage.py`
- Create: `backend/config/__init__.py`
- Create: `backend/config/settings.py`
- Create: `backend/config/urls.py`
- Create: `backend/config/wsgi.py`
- Create: `backend/separator/__init__.py`

- [x] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "audio-separator-backend"
version = "0.1.0"
description = "AI Audio Separator Backend"
requires-python = ">=3.11"
dependencies = [
    "django>=5.0,<6.0",
    "djangorestframework>=3.15,<4.0",
    "django-cors-headers>=4.4,<5.0",
    "spleeter>=2.4,<3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-django>=4.8",
    "pytest-cov>=5.0",
]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
pythonpath = ["."]
testpaths = ["tests"]
```

- [x] **Step 2: 创建 Django 项目结构**

运行以下命令初始化目录：

```bash
cd /Users/lixueduan/17x/idea/vocalremover
mkdir -p backend/config backend/separator backend/tests
```

创建 `backend/manage.py`：

```python
#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
```

创建 `backend/config/__init__.py`（空文件）。

创建 `backend/separator/__init__.py`（空文件）。

创建 `backend/tests/__init__.py`（空文件）。

- [x] **Step 3: 编写 settings.py**

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-dev-key-change-in-production"

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "separator",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Media files
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# CORS
CORS_ALLOW_ALL_ORIGINS = True

# File upload limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
}
```

- [x] **Step 4: 编写 urls.py**

`backend/config/urls.py`:

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("separator.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [x] **Step 5: 编写 wsgi.py**

`backend/config/wsgi.py`:

```python
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
```

- [x] **Step 6: 安装依赖并验证 Django 可运行**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv sync --extra dev
uv run python manage.py check
```

预期输出：`System check identified no issues (0 silenced).`

- [x] **Step 7: 提交**

```bash
git add backend/pyproject.toml backend/manage.py backend/config/ backend/separator/__init__.py backend/tests/__init__.py
git commit -m "chore: initialize Django project with DRF and CORS"
```

---

## Task 2: Task 模型

**文件：**
- Create: `backend/separator/models.py`
- Create: `backend/tests/test_models.py`
- Modify: `backend/config/settings.py`（已配置，无需改动）

- [x] **Step 1: 编写模型测试**

`backend/tests/conftest.py`:

```python
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
```

`backend/tests/test_models.py`:

```python
import pytest
from django.utils import timezone

from separator.models import Task


@pytest.mark.django_db
class TestTaskModel:
    def test_create_task_with_defaults(self, sample_task_data):
        task = Task.objects.create(**sample_task_data)
        assert task.status == Task.Status.PENDING
        assert task.mode == "2stems"
        assert task.original_filename == "test.mp3"
        assert task.id is not None
        assert task.created_at is not None
        assert task.updated_at is not None
        assert task.completed_at is None
        assert task.error_message is None
        assert task.stems == {}

    def test_task_has_uuid_primary_key(self, sample_task_data):
        task = Task.objects.create(**sample_task_data)
        assert len(str(task.id)) == 36  # UUID format with hyphens

    def test_status_transitions(self, sample_task_data):
        task = Task.objects.create(**sample_task_data)
        assert task.status == Task.Status.PENDING

        task.status = Task.Status.PROCESSING
        task.save()
        task.refresh_from_db()
        assert task.status == Task.Status.PROCESSING

        task.status = Task.Status.COMPLETED
        task.completed_at = timezone.now()
        task.save()
        task.refresh_from_db()
        assert task.status == Task.Status.COMPLETED
        assert task.completed_at is not None

    def test_failed_status_with_error_message(self, sample_task_data):
        task = Task.objects.create(**sample_task_data)
        task.status = Task.Status.FAILED
        task.error_message = "Spleeter inference failed"
        task.save()
        task.refresh_from_db()
        assert task.status == Task.Status.FAILED
        assert task.error_message == "Spleeter inference failed"

    def test_stems_json_field(self, sample_task_data):
        stems = {"vocals": "/media/stems/abc/vocals.wav"}
        task = Task.objects.create(**sample_task_data, stems=stems)
        task.refresh_from_db()
        assert task.stems == stems

    def test_mode_choices(self, sample_task_data):
        task_2 = Task.objects.create(**{**sample_task_data, "mode": "2stems"})
        task_4 = Task.objects.create(**{**sample_task_data, "mode": "4stems"})
        assert task_2.mode == "2stems"
        assert task_4.mode == "4stems"
```

- [x] **Step 2: 运行测试确认失败**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run pytest tests/test_models.py -v
```

预期：FAIL — `ModuleNotFoundError: No module named 'separator.models'`

- [x] **Step 3: 编写 Task 模型**

`backend/separator/models.py`:

```python
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
```

- [x] **Step 4: 运行测试确认通过**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run pytest tests/test_models.py -v
```

预期：全部 PASS

- [x] **Step 5: 运行迁移**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run python manage.py makemigrations separator
uv run python manage.py migrate
```

预期：创建 `separator/migrations/0001_initial.py`，数据库表创建成功。

- [x] **Step 6: 验证 Django check**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run python manage.py check
```

预期：`System check identified no issues (0 silenced).`

- [x] **Step 7: 提交**

```bash
git add backend/separator/models.py backend/separator/migrations/ backend/tests/conftest.py backend/tests/test_models.py
git commit -m "feat: add Task model with UUID primary key and status transitions"
```

---

## Task 3: Task 序列化器

**文件：**
- Create: `backend/separator/serializers.py`
- Create: `backend/tests/test_serializers.py`

- [x] **Step 1: 编写序列化器测试**

`backend/tests/test_serializers.py`:

```python
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from separator.models import Task
from separator.serializers import TaskCreateSerializer, TaskSerializer


@pytest.mark.django_db
class TestTaskSerializer:
    def test_serialize_task(self, sample_task_data):
        task = Task.objects.create(**sample_task_data)
        serializer = TaskSerializer(task)
        data = serializer.data
        assert data["id"] == str(task.id)
        assert data["status"] == "PENDING"
        assert data["mode"] == "2stems"
        assert data["original_filename"] == "test.mp3"
        assert "created_at" in data
        assert "stems" in data

    def test_serialize_task_with_stems(self, sample_task_data):
        stems = {"vocals": "vocals.wav"}
        task = Task.objects.create(**sample_task_data, stems=stems)
        serializer = TaskSerializer(task)
        assert serializer.data["stems"] == stems


@pytest.mark.django_db
class TestTaskCreateSerializer:
    def test_valid_2stems_upload(self):
        audio = SimpleUploadedFile("song.mp3", b"audio content", content_type="audio/mpeg")
        serializer = TaskCreateSerializer(data={"file": audio, "mode": "2stems"})
        assert serializer.is_valid(), serializer.errors
        task = serializer.save()
        assert task.mode == "2stems"
        assert task.original_filename == "song.mp3"
        assert task.status == Task.Status.PENDING

    def test_valid_4stems_upload(self):
        audio = SimpleUploadedFile("song.wav", b"audio content", content_type="audio/wav")
        serializer = TaskCreateSerializer(data={"file": audio, "mode": "4stems"})
        assert serializer.is_valid(), serializer.errors
        task = serializer.save()
        assert task.mode == "4stems"

    def test_missing_mode(self):
        audio = SimpleUploadedFile("song.mp3", b"audio content", content_type="audio/mpeg")
        serializer = TaskCreateSerializer(data={"file": audio})
        assert not serializer.is_valid()
        assert "mode" in serializer.errors

    def test_invalid_mode(self):
        audio = SimpleUploadedFile("song.mp3", b"audio content", content_type="audio/mpeg")
        serializer = TaskCreateSerializer(data={"file": audio, "mode": "3stems"})
        assert not serializer.is_valid()
        assert "mode" in serializer.errors

    def test_unsupported_format(self):
        audio = SimpleUploadedFile("song.txt", b"not audio", content_type="text/plain")
        serializer = TaskCreateSerializer(data={"file": audio, "mode": "2stems"})
        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_file_too_large(self):
        large_content = b"x" * (20 * 1024 * 1024 + 1)
        audio = SimpleUploadedFile("song.mp3", large_content, content_type="audio/mpeg")
        serializer = TaskCreateSerializer(data={"file": audio, "mode": "2stems"})
        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_supported_formats(self):
        for ext, content_type in [
            ("mp3", "audio/mpeg"),
            ("wav", "audio/wav"),
            ("flac", "audio/flac"),
            ("ogg", "audio/ogg"),
            ("m4a", "audio/mp4"),
        ]:
            audio = SimpleUploadedFile(
                f"song.{ext}", b"audio content", content_type=content_type
            )
            serializer = TaskCreateSerializer(data={"file": audio, "mode": "2stems"})
            assert serializer.is_valid(), f"{ext} should be valid: {serializer.errors}"

    def test_missing_file(self):
        serializer = TaskCreateSerializer(data={"mode": "2stems"})
        assert not serializer.is_valid()
        assert "file" in serializer.errors
```

- [x] **Step 2: 运行测试确认失败**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run pytest tests/test_serializers.py -v
```

预期：FAIL — `ModuleNotFoundError: No module named 'separator.serializers'`

- [x] **Step 3: 编写序列化器**

`backend/separator/serializers.py`:

```python
from rest_framework import serializers

from separator.models import Task

ALLOWED_EXTENSIONS = {"mp3", "wav", "flac", "ogg", "m4a"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


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
        # Save uploaded file to media/uploads/{task_id}/original.{ext}
        from django.core.files.storage import default_storage
        from pathlib import Path

        ext = Path(uploaded_file.name).suffix
        upload_path = f"uploads/{task.id}/original{ext}"
        default_storage.save(upload_path, uploaded_file)
        return task
```

- [x] **Step 4: 运行测试确认通过**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run pytest tests/test_serializers.py -v
```

预期：全部 PASS

- [x] **Step 5: 提交**

```bash
git add backend/separator/serializers.py backend/tests/test_serializers.py
git commit -m "feat: add Task serializers with file validation"
```

---

## Task 4: API 视图和 URL 路由

**文件：**
- Create: `backend/separator/views.py`
- Create: `backend/separator/urls.py`
- Create: `backend/tests/test_views.py`

- [x] **Step 1: 编写视图测试**

`backend/tests/test_views.py`:

```python
import io
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from separator.models import Task


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_task(db):
    """Create a task and return it."""
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
        import uuid
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
        # Verify ZIP contents
        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer) as zf:
            names = zf.namelist()
            assert "vocals.wav" in names
            assert "accompaniment.wav" in names
```

- [x] **Step 2: 运行测试确认失败**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run pytest tests/test_views.py -v
```

预期：FAIL — `ModuleNotFoundError: No module named 'separator.views'`

- [x] **Step 3: 编写视图**

`backend/separator/views.py`:

```python
import io
import os
import zipfile
from pathlib import Path

from django.http import FileResponse, Http404, HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from separator.models import Task
from separator.serializers import TaskCreateSerializer, TaskSerializer

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


@api_view(["GET"])
def stem_download(request, task_id, stem_name):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response(
            {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
        )

    if stem_name not in ALLOWED_STEM_NAMES:
        return Response(
            {"error": "Invalid stem name"}, status=status.HTTP_400_BAD_REQUEST
        )

    stem_path = Path(settings.MEDIA_ROOT) / "stems" / str(task_id) / f"{stem_name}.wav"
    if not stem_path.exists():
        return Response(
            {"error": "Stem not found"}, status=status.HTTP_404_NOT_FOUND
        )

    response = FileResponse(open(stem_path, "rb"), content_type="audio/wav")
    response["Content-Disposition"] = f'attachment; filename="{stem_name}.wav"'
    return response


@api_view(["GET"])
def stem_stream(request, task_id, stem_name):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response(
            {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
        )

    if stem_name not in ALLOWED_STEM_NAMES:
        return Response(
            {"error": "Invalid stem name"}, status=status.HTTP_400_BAD_REQUEST
        )

    stem_path = Path(settings.MEDIA_ROOT) / "stems" / str(task_id) / f"{stem_name}.wav"
    if not stem_path.exists():
        return Response(
            {"error": "Stem not found"}, status=status.HTTP_404_NOT_FOUND
        )

    response = FileResponse(open(stem_path, "rb"), content_type="audio/wav")
    response["Accept-Ranges"] = "bytes"
    return response


@api_view(["GET"])
def download_all_stems(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response(
            {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
        )

    stem_dir = Path(settings.MEDIA_ROOT) / "stems" / str(task_id)
    if not stem_dir.exists():
        return Response(
            {"error": "Stems not found"}, status=status.HTTP_404_NOT_FOUND
        )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for stem_file in stem_dir.glob("*.wav"):
            zf.write(stem_file, stem_file.name)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{task_id}_stems.zip"'
    return response
```

- [x] **Step 4: 编写 URL 路由**

`backend/separator/urls.py`:

```python
from django.urls import path

from separator import views

urlpatterns = [
    path("tasks/", views.create_task, name="create-task"),
    path("tasks/<uuid:task_id>/", views.get_task, name="get-task"),
    path("tasks/<uuid:task_id>/stems/", views.list_stems, name="list-stems"),
    path(
        "tasks/<uuid:task_id>/stems/download-all/",
        views.download_all_stems,
        name="download-all-stems",
    ),
    path(
        "tasks/<uuid:task_id>/stems/<str:stem_name>/",
        views.stem_download,
        name="stem-download",
    ),
    path(
        "tasks/<uuid:task_id>/stems/<str:stem_name>/stream/",
        views.stem_stream,
        name="stem-stream",
    ),
]
```

- [x] **Step 5: 修复视图中缺少的 import**

在 `backend/separator/views.py` 顶部添加缺少的 import：

```python
from django.conf import settings
```

- [x] **Step 6: 运行测试确认通过**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run pytest tests/test_views.py -v
```

预期：全部 PASS

- [x] **Step 7: 提交**

```bash
git add backend/separator/views.py backend/separator/urls.py backend/tests/test_views.py
git commit -m "feat: add task API endpoints with file validation and stem download"
```

---

## Task 5: Spleeter 分离封装

**文件：**
- Create: `backend/separator/separation.py`
- Create: `backend/tests/test_separation.py`

- [x] **Step 1: 编写分离测试**

`backend/tests/test_separation.py`:

```python
from pathlib import Path
from unittest.mock import MagicMock, patch

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
        # No upload directory created

        with pytest.raises(SeparationError, match="Upload file not found"):
            separate_audio(task, media_root=tmp_path)
```

- [x] **Step 2: 运行测试确认失败**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run pytest tests/test_separation.py -v
```

预期：FAIL — `ModuleNotFoundError: No module named 'separator.separation'`

- [x] **Step 3: 编写分离封装**

`backend/separator/separation.py`:

```python
import logging
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
    upload_dir = media_root / "uploads" / task_id
    if not upload_dir.exists():
        raise SeparationError(f"Upload file not found for task {task_id}")
    # Find the first file in the upload directory
    files = list(upload_dir.iterdir())
    if not files:
        raise SeparationError(f"Upload file not found for task {task_id}")
    return files[0]


def _run_spleeter(input_path: str, output_dir: str, preset: str) -> dict[str, str]:
    """Call Spleeter's Python API to separate audio.

    Returns dict mapping stem names to output file paths.
    """
    from spleeter.separator import Separator

    separator = Separator(preset)
    separator.separate_to_file(input_path, output_dir)

    # Determine output paths based on preset
    input_stem = Path(input_path).stem
    mode = "2stems" if "2stems" in preset else "4stems"
    names = ["vocals", "accompaniment"] if mode == "2stems" else ["vocals", "drums", "bass", "other"]

    result = {}
    for name in names:
        stem_path = Path(output_dir) / input_stem / f"{name}.wav"
        if stem_path.exists():
            result[name] = str(stem_path)
    return result


def separate_audio(task: Task, media_root: Path | None = None) -> dict[str, str]:
    """Invoke Spleeter to separate audio file.

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

    logger.info("Starting separation for task %s (mode=%s)", task.id, task.mode)

    try:
        result = _run_spleeter(str(upload_file), output_dir, preset)
    except Exception as exc:
        logger.error("Spleeter failed for task %s: %s", task.id, exc)
        raise SeparationError(str(exc)) from exc

    logger.info("Separation completed for task %s: %s", task.id, list(result.keys()))
    return result
```

- [x] **Step 4: 运行测试确认通过**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run pytest tests/test_separation.py -v
```

预期：全部 PASS

- [x] **Step 5: 提交**

```bash
git add backend/separator/separation.py backend/tests/test_separation.py
git commit -m "feat: add Spleeter audio separation wrapper"
```

---

## Task 6: Worker 管理命令

**文件：**
- Create: `backend/separator/worker.py`
- Create: `backend/separator/management/__init__.py`
- Create: `backend/separator/management/commands/__init__.py`
- Create: `backend/separator/management/commands/run_worker.py`
- Create: `backend/tests/test_worker.py`

- [x] **Step 1: 编写 Worker 测试**

`backend/tests/test_worker.py`:

```python
import signal
from datetime import timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from separator.models import Task
from separator.worker import Worker


@pytest.fixture
def worker(tmp_path):
    return Worker(media_root=tmp_path, poll_interval=0.01)


@pytest.mark.django_db
class TestWorker:
    def test_process_pending_task_success(self, worker, tmp_path):
        task = Task.objects.create(
            mode="2stems",
            original_filename="song.mp3",
            file_size=1024,
        )
        assert task.status == Task.Status.PENDING

        with patch("separator.worker.separate_audio") as mock_sep:
            mock_sep.return_value = {
                "vocals": str(tmp_path / "stems" / str(task.id) / "vocals.wav"),
                "accompaniment": str(tmp_path / "stems" / str(task.id) / "accompaniment.wav"),
            }
            worker._process_task(task)

        task.refresh_from_db()
        assert task.status == Task.Status.COMPLETED
        assert task.completed_at is not None
        assert "vocals" in task.stems
        assert "accompaniment" in task.stems

    def test_process_task_failure(self, worker, tmp_path):
        task = Task.objects.create(
            mode="2stems",
            original_filename="corrupt.mp3",
            file_size=100,
        )

        with patch("separator.worker.separate_audio") as mock_sep:
            mock_sep.side_effect = RuntimeError("Spleeter crashed")
            worker._process_task(task)

        task.refresh_from_db()
        assert task.status == Task.Status.FAILED
        assert task.error_message == "Spleeter crashed"
        assert task.completed_at is None

    def test_recover_stuck_processing_tasks(self, worker):
        # Create a task stuck in PROCESSING for > 30 minutes
        stuck_task = Task.objects.create(
            mode="2stems",
            original_filename="stuck.mp3",
            file_size=512,
            status=Task.Status.PROCESSING,
        )
        # Backdate updated_at
        Task.objects.filter(id=stuck_task.id).update(
            updated_at=timezone.now() - timedelta(minutes=31)
        )

        worker._recover_stuck_tasks()
        stuck_task.refresh_from_db()
        assert stuck_task.status == Task.Status.FAILED
        assert "timeout" in stuck_task.error_message.lower()

    def test_recover_ignores_recent_processing_tasks(self, worker):
        recent_task = Task.objects.create(
            mode="2stems",
            original_filename="recent.mp3",
            file_size=512,
            status=Task.Status.PROCESSING,
        )

        worker._recover_stuck_tasks()
        recent_task.refresh_from_db()
        assert recent_task.status == Task.Status.PROCESSING

    def test_graceful_shutdown(self, worker):
        worker._shutdown = False
        worker._handle_shutdown(signal.SIGTERM, None)
        assert worker._shutdown is True
```

- [x] **Step 2: 运行测试确认失败**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run pytest tests/test_worker.py -v
```

预期：FAIL — `ModuleNotFoundError: No module named 'separator.worker'`

- [x] **Step 3: 编写 Worker 逻辑**

`backend/separator/worker.py`:

```python
import logging
import signal
import time
from datetime import timedelta
from pathlib import Path

from django.db import transaction
from django.utils import timezone

from separator.models import Task
from separator.separation import SeparationError, separate_audio

logger = logging.getLogger(__name__)

STUCK_TIMEOUT_MINUTES = 30


class Worker:
    def __init__(self, media_root: Path | None = None, poll_interval: float = 2.0):
        self._shutdown = False
        self._media_root = media_root
        self._poll_interval = poll_interval

    def _handle_shutdown(self, signum, frame):
        logger.info("Received signal %s, shutting down gracefully...", signum)
        self._shutdown = True

    def _recover_stuck_tasks(self):
        cutoff = timezone.now() - timedelta(minutes=STUCK_TIMEOUT_MINUTES)
        stuck_tasks = Task.objects.filter(
            status=Task.Status.PROCESSING, updated_at__lt=cutoff
        )
        count = stuck_tasks.update(
            status=Task.Status.FAILED,
            error_message="Task timed out: no heartbeat for over 30 minutes",
        )
        if count > 0:
            logger.warning("Recovered %d stuck PROCESSING tasks", count)

    def _process_task(self, task: Task):
        task.status = Task.Status.PROCESSING
        task.save(update_fields=["status", "updated_at"])
        logger.info("Processing task %s", task.id)

        try:
            stems = separate_audio(task, media_root=self._media_root)
            task.stems = stems
            task.status = Task.Status.COMPLETED
            task.completed_at = timezone.now()
            task.save()
            logger.info("Task %s completed with stems: %s", task.id, list(stems.keys()))
        except (SeparationError, Exception) as exc:
            task.status = Task.Status.FAILED
            task.error_message = str(exc)
            task.save(update_fields=["status", "error_message", "updated_at"])
            logger.error("Task %s failed: %s", task.id, exc)

    def _claim_pending_task(self) -> Task | None:
        with transaction.atomic():
            task = (
                Task.objects.select_for_update(skip_locked=True)
                .filter(status=Task.Status.PENDING)
                .order_by("created_at")
                .first()
            )
            if task:
                task.status = Task.Status.PROCESSING
                task.save(update_fields=["status", "updated_at"])
        return task

    def run(self):
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        logger.info("Worker started (poll_interval=%.1fs)", self._poll_interval)
        self._recover_stuck_tasks()

        while not self._shutdown:
            try:
                task = self._claim_pending_task()
                if task:
                    self._process_task(task)
                else:
                    time.sleep(self._poll_interval)
            except Exception:
                logger.exception("Unexpected error in worker loop")
                time.sleep(self._poll_interval)

        logger.info("Worker stopped")
```

- [x] **Step 4: 创建管理命令**

创建目录结构：

```bash
mkdir -p /Users/lixueduan/17x/idea/vocalremover/backend/separator/management/commands
```

`backend/separator/management/__init__.py`（空文件）。

`backend/separator/management/commands/__init__.py`（空文件）。

`backend/separator/management/commands/run_worker.py`:

```python
import logging

from django.core.management.base import BaseCommand

from separator.worker import Worker


class Command(BaseCommand):
    help = "Run the audio separation worker"

    def add_arguments(self, parser):
        parser.add_argument(
            "--poll-interval",
            type=float,
            default=2.0,
            help="Seconds between DB polls (default: 2.0)",
        )

    def handle(self, *args, **options):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        worker = Worker(poll_interval=options["poll_interval"])
        worker.run()
```

- [x] **Step 5: 运行测试确认通过**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run pytest tests/test_worker.py -v
```

预期：全部 PASS

- [x] **Step 6: 提交**

```bash
git add backend/separator/worker.py backend/separator/management/ backend/tests/test_worker.py
git commit -m "feat: add Worker with task polling, Spleeter integration, and graceful shutdown"
```

---

## Task 7: 清理旧任务管理命令

**文件：**
- Create: `backend/separator/management/commands/cleanup_old_tasks.py`

- [x] **Step 1: 编写清理命令**

`backend/separator/management/commands/cleanup_old_tasks.py`:

```python
import logging
import shutil
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from separator.models import Task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Delete tasks older than 24 hours and their associated files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--max-age-hours",
            type=int,
            default=24,
            help="Max age in hours (default: 24)",
        )

    def handle(self, *args, **options):
        max_age = options["max_age_hours"]
        cutoff = timezone.now() - timedelta(hours=max_age)
        old_tasks = Task.objects.filter(created_at__lt=cutoff)

        count = 0
        for task in old_tasks:
            self._delete_task_files(task)
            task.delete()
            count += 1

        logger.info("Cleanup completed: deleted %d tasks older than %d hours", count, max_age)
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} old tasks"))

    def _delete_task_files(self, task: Task):
        media_root = Path(settings.MEDIA_ROOT)
        for subdir in ("uploads", "stems"):
            task_dir = media_root / subdir / str(task.id)
            if task_dir.exists():
                shutil.rmtree(task_dir)
                logger.info("Deleted %s", task_dir)
```

- [x] **Step 2: 验证命令可运行**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run python manage.py cleanup_old_tasks --help
```

预期：显示命令帮助信息，包含 `--max-age-hours` 参数。

- [x] **Step 3: 提交**

```bash
git add backend/separator/management/commands/cleanup_old_tasks.py
git commit -m "feat: add cleanup_old_tasks management command"
```

---

## Task 8: Django Admin 配置

**文件：**
- Modify: `backend/separator/admin.py`

- [x] **Step 1: 编写 Admin 配置**

`backend/separator/admin.py`:

```python
from django.contrib import admin

from separator.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "short_id",
        "status",
        "mode",
        "original_filename",
        "file_size_display",
        "created_at",
    )
    list_filter = ("status", "mode")
    search_fields = ("original_filename", "id")
    readonly_fields = ("id", "created_at", "updated_at", "completed_at", "error_message", "stems")
    actions = ("mark_as_failed",)

    def short_id(self, obj):
        return str(obj.id)[:8]

    short_id.short_description = "ID"

    def file_size_display(self, obj):
        if obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        return f"{obj.file_size / (1024 * 1024):.1f} MB"

    file_size_display.short_description = "Size"

    @admin.action(description="Mark selected tasks as Failed")
    def mark_as_failed(self, request, queryset):
        count = queryset.filter(status=Task.Status.PROCESSING).update(
            status=Task.Status.FAILED,
            error_message="Manually marked as failed by admin",
        )
        self.message_user(request, f"Marked {count} tasks as failed")
```

- [x] **Step 2: 验证 Admin 配置**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run python manage.py check
```

预期：`System check identified no issues (0 silenced).`

- [x] **Step 3: 提交**

```bash
git add backend/separator/admin.py
git commit -m "feat: configure Django Admin with task list, filters, and actions"
```

---

## Task 9: 初始化 Vue 3 前端项目

**文件：**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.app.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/env.d.ts`
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/types/index.ts`

- [x] **Step 1: 创建前端项目**

```bash
cd /Users/lixueduan/17x/idea/vocalremover
npm create vue@latest frontend -- --typescript --router --no-pinia --no-vitest --no-e2e --no-eslint --no-prettier
```

- [x] **Step 2: 安装依赖**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/frontend
npm install
npm install axios wavesurfer.js element-plus
npm install -D @vue/test-utils jsdom vitest
```

- [x] **Step 3: 配置 Vite 代理**

`frontend/vite.config.ts`：

```typescript
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/media': 'http://localhost:8000',
    },
  },
})
```

- [x] **Step 4: 创建 TypeScript 类型定义**

`frontend/src/types/index.ts`：

```typescript
export interface Task {
  id: string
  status: TaskStatus
  mode: SeparationMode
  original_filename: string
  file_size: number
  created_at: string
  updated_at: string
  completed_at: string | null
  error_message: string | null
  stems: Record<string, StemInfo>
}

export type TaskStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
export type SeparationMode = '2stems' | '4stems'

export interface StemInfo {
  filename: string
  size?: number
}

export interface StemName extends String {
  __brand: 'StemName'
}

export const VALID_STEM_NAMES = [
  'vocals',
  'accompaniment',
  'drums',
  'bass',
  'other',
] as const

export type StemNameType = (typeof VALID_STEM_NAMES)[number]
```

- [x] **Step 5: 创建路由配置**

`frontend/src/router/index.ts`：

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/result/:taskId',
      name: 'result',
      component: () => import('@/views/ResultView.vue'),
    },
  ],
})

export default router
```

- [x] **Step 6: 创建 App.vue**

`frontend/src/App.vue`：

```vue
<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <el-config-provider>
    <div id="app-container">
      <RouterView />
    </div>
  </el-config-provider>
</template>

<style scoped>
#app-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 20px;
}
</style>
```

- [x] **Step 7: 更新 main.ts**

`frontend/src/main.ts`：

```typescript
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(router)
app.use(ElementPlus)
app.mount('#app')
```

- [x] **Step 8: 验证前端可运行**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/frontend
npm run dev
```

预期：开发服务器在 `http://localhost:5173` 启动（运行几秒后 Ctrl+C 停止）。

- [x] **Step 9: 提交**

```bash
git add frontend/
git commit -m "chore: initialize Vue 3 frontend with TypeScript, Vite, and Element Plus"
```

---

## Task 10: API 客户端和 Composables

**文件：**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/composables/useTask.ts`
- Create: `frontend/src/composables/useAudioPlayer.ts`
- Create: `frontend/src/__tests__/api-client.test.ts`

- [x] **Step 1: 编写 API 客户端测试**

`frontend/src/__tests__/api-client.test.ts`：

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { createTask, getTaskStatus, getStems } from '@/api/client'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('createTask', () => {
    it('sends multipart POST with file and mode', async () => {
      const mockResponse = {
        data: {
          id: 'abc-123',
          status: 'PENDING',
          mode: '2stems',
          original_filename: 'song.mp3',
        },
      }
      mockedAxios.post.mockResolvedValue(mockResponse)

      const formData = new FormData()
      formData.append('file', new File(['audio'], 'song.mp3'))
      formData.append('mode', '2stems')

      const result = await createTask(formData)
      expect(result.id).toBe('abc-123')
      expect(result.status).toBe('PENDING')
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/tasks/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    })

    it('throws on upload failure', async () => {
      mockedAxios.post.mockRejectedValue({
        response: { data: { file: ['Unsupported format'] } },
      })

      const formData = new FormData()
      await expect(createTask(formData)).rejects.toThrow()
    })
  })

  describe('getTaskStatus', () => {
    it('fetches task by id', async () => {
      const mockResponse = {
        data: { id: 'abc-123', status: 'COMPLETED', stems: {} },
      }
      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await getTaskStatus('abc-123')
      expect(result.status).toBe('COMPLETED')
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/tasks/abc-123/')
    })
  })

  describe('getStems', () => {
    it('fetches stems for completed task', async () => {
      const mockStems = {
        vocals: { filename: 'vocals.wav' },
        accompaniment: { filename: 'accompaniment.wav' },
      }
      mockedAxios.get.mockResolvedValue({ data: mockStems })

      const result = await getStems('abc-123')
      expect(result).toEqual(mockStems)
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/tasks/abc-123/stems/')
    })
  })
})
```

- [x] **Step 2: 运行测试确认失败**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/frontend
npx vitest run src/__tests__/api-client.test.ts
```

预期：FAIL — `Cannot find module '@/api/client'`

- [x] **Step 3: 编写 API 客户端**

`frontend/src/api/client.ts`：

```typescript
import axios from 'axios'
import type { Task } from '@/types'

const apiClient = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
})

export async function createTask(formData: FormData): Promise<Task> {
  const response = await apiClient.post<Task>('/api/tasks/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function getTaskStatus(taskId: string): Promise<Task> {
  const response = await apiClient.get<Task>(`/api/tasks/${taskId}/`)
  return response.data
}

export async function getStems(
  taskId: string
): Promise<Record<string, { filename: string; size?: number }>> {
  const response = await apiClient.get(`/api/tasks/${taskId}/stems/`)
  return response.data
}

export function getStemStreamUrl(taskId: string, stemName: string): string {
  return `/api/tasks/${taskId}/stems/${stemName}/stream/`
}

export function getStemDownloadUrl(taskId: string, stemName: string): string {
  return `/api/tasks/${taskId}/stems/${stemName}/`
}

export function getDownloadAllUrl(taskId: string): string {
  return `/api/tasks/${taskId}/stems/download-all/`
}
```

- [x] **Step 4: 运行测试确认通过**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/frontend
npx vitest run src/__tests__/api-client.test.ts
```

预期：全部 PASS

- [x] **Step 5: 编写 useTask composable**

`frontend/src/composables/useTask.ts`：

```typescript
import { ref, onUnmounted } from 'vue'
import type { Task } from '@/types'
import { getTaskStatus } from '@/api/client'

const POLL_INTERVAL_MS = 3000
const MAX_CONSECUTIVE_ERRORS = 3

export function useTask(taskId: string) {
  const task = ref<Task | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  let pollTimer: ReturnType<typeof setInterval> | null = null
  let consecutiveErrors = 0

  async function fetchTask() {
    try {
      isLoading.value = true
      task.value = await getTaskStatus(taskId)
      error.value = null
      consecutiveErrors = 0

      if (task.value.status === 'COMPLETED' || task.value.status === 'FAILED') {
        stopPolling()
      }
    } catch (err) {
      consecutiveErrors += 1
      if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
        error.value = 'Network error, please refresh the page'
        stopPolling()
      }
    } finally {
      isLoading.value = false
    }
  }

  function startPolling() {
    if (pollTimer) return
    fetchTask()
    pollTimer = setInterval(fetchTask, POLL_INTERVAL_MS)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  onUnmounted(stopPolling)

  return {
    task,
    isLoading,
    error,
    startPolling,
    stopPolling,
  }
}
```

- [x] **Step 6: 编写 useAudioPlayer composable**

`frontend/src/composables/useAudioPlayer.ts`：

```typescript
import { ref, onUnmounted, type Ref } from 'vue'
import WaveSurfer from 'wavesurfer.js'

export function useAudioPlayer(waveformRef: Ref<HTMLElement | null>, url: string) {
  const isPlaying = ref(false)
  const currentTime = ref(0)
  const duration = ref(0)
  const isLoading = ref(true)
  const hasError = ref(false)
  let wavesurfer: WaveSurfer | null = null

  function init() {
    if (!waveformRef.value) return

    wavesurfer = WaveSurfer.create({
      container: waveformRef.value,
      url,
      height: 80,
      waveColor: '#409EFF',
      progressColor: '#1D9BF0',
      cursorColor: '#333',
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
    })

    wavesurfer.on('ready', () => {
      isLoading.value = false
      duration.value = wavesurfer!.getDuration()
    })

    wavesurfer.on('play', () => {
      isPlaying.value = true
    })

    wavesurfer.on('pause', () => {
      isPlaying.value = false
    })

    wavesurfer.on('timeupdate', (time: number) => {
      currentTime.value = time
    })

    wavesurfer.on('error', () => {
      hasError.value = true
      isLoading.value = false
    })
  }

  function play() {
    wavesurfer?.play()
  }

  function pause() {
    wavesurfer?.pause()
  }

  function togglePlay() {
    wavesurfer?.playPause()
  }

  function seekTo(time: number) {
    wavesurfer?.seekTo(time / duration.value)
  }

  function destroy() {
    wavesurfer?.destroy()
    wavesurfer = null
  }

  onUnmounted(destroy)

  return {
    isPlaying,
    currentTime,
    duration,
    isLoading,
    hasError,
    init,
    play,
    pause,
    togglePlay,
    seekTo,
    destroy,
  }
}
```

- [x] **Step 7: 提交**

```bash
git add frontend/src/api/ frontend/src/composables/ frontend/src/__tests__/api-client.test.ts frontend/src/types/
git commit -m "feat: add API client, useTask and useAudioPlayer composables"
```

---

## Task 11: FileUploader 和 ModeSelector 组件

**文件：**
- Create: `frontend/src/components/FileUploader.vue`
- Create: `frontend/src/components/ModeSelector.vue`
- Create: `frontend/src/__tests__/FileUploader.test.ts`
- Create: `frontend/src/__tests__/ModeSelector.test.ts`

- [x] **Step 1: 编写 FileUploader 测试**

`frontend/src/__tests__/FileUploader.test.ts`：

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FileUploader from '@/components/FileUploader.vue'

describe('FileUploader', () => {
  it('renders upload area', () => {
    const wrapper = mount(FileUploader)
    expect(wrapper.find('[data-testid="upload-area"]').exists()).toBe(true)
  })

  it('accepts valid audio file via input', async () => {
    const wrapper = mount(FileUploader)
    const input = wrapper.find('input[type="file"]')
    const file = new File(['audio content'], 'song.mp3', { type: 'audio/mpeg' })

    Object.defineProperty(input.element, 'files', {
      value: [file],
    })
    await input.trigger('change')

    expect(wrapper.emitted('file-selected')).toBeTruthy()
    expect(wrapper.emitted('file-selected')![0]).toEqual([file])
  })

  it('rejects unsupported file format', async () => {
    const wrapper = mount(FileUploader)
    const input = wrapper.find('input[type="file"]')
    const file = new File(['text'], 'readme.txt', { type: 'text/plain' })

    Object.defineProperty(input.element, 'files', {
      value: [file],
    })
    await input.trigger('change')

    expect(wrapper.emitted('file-selected')).toBeFalsy()
    expect(wrapper.emitted('error')).toBeTruthy()
  })

  it('rejects file exceeding 20MB', async () => {
    const wrapper = mount(FileUploader)
    const input = wrapper.find('input[type="file"]')
    const largeFile = new File(['x'.repeat(20 * 1024 * 1024 + 1)], 'large.mp3', {
      type: 'audio/mpeg',
    })

    Object.defineProperty(input.element, 'files', {
      value: [largeFile],
    })
    await input.trigger('change')

    expect(wrapper.emitted('file-selected')).toBeFalsy()
    expect(wrapper.emitted('error')).toBeTruthy()
  })

  it('shows selected file name', async () => {
    const wrapper = mount(FileUploader)
    const input = wrapper.find('input[type="file"]')
    const file = new File(['audio'], 'my-song.mp3', { type: 'audio/mpeg' })

    Object.defineProperty(input.element, 'files', {
      value: [file],
    })
    await input.trigger('change')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('my-song.mp3')
  })
})
```

- [x] **Step 2: 运行测试确认失败**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/frontend
npx vitest run src/__tests__/FileUploader.test.ts
```

预期：FAIL — `Cannot find module '@/components/FileUploader.vue'`

- [x] **Step 3: 编写 FileUploader 组件**

`frontend/src/components/FileUploader.vue`：

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const emit = defineEmits<{
  'file-selected': [file: File]
  error: [message: string]
}>()

const ALLOWED_EXTENSIONS = ['mp3', 'wav', 'flac', 'ogg', 'm4a']
const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB

const selectedFile = ref<File | null>(null)
const isDragOver = ref(false)

function validateFile(file: File): boolean {
  const extension = file.name.split('.').pop()?.toLowerCase() ?? ''
  if (!ALLOWED_EXTENSIONS.includes(extension)) {
    const msg = `Unsupported format. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`
    ElMessage.error(msg)
    emit('error', msg)
    return false
  }
  if (file.size > MAX_FILE_SIZE) {
    const msg = 'File too large. Max size: 20MB'
    ElMessage.error(msg)
    emit('error', msg)
    return false
  }
  return true
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (validateFile(file)) {
    selectedFile.value = file
    emit('file-selected', file)
  }
}

function handleDrop(event: DragEvent) {
  isDragOver.value = false
  const file = event.dataTransfer?.files[0]
  if (!file) return
  if (validateFile(file)) {
    selectedFile.value = file
    emit('file-selected', file)
  }
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  isDragOver.value = true
}

function handleDragLeave() {
  isDragOver.value = false
}

function triggerFileInput() {
  const input = document.getElementById('file-input') as HTMLInputElement
  input?.click()
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<template>
  <div
    data-testid="upload-area"
    class="upload-area"
    :class="{ 'drag-over': isDragOver }"
    @drop.prevent="handleDrop"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
    @click="triggerFileInput"
  >
    <input
      id="file-input"
      type="file"
      :accept="ALLOWED_EXTENSIONS.map((e) => `.${e}`).join(',')"
      style="display: none"
      @change="handleFileChange"
    />
    <el-icon :size="48" class="upload-icon"><UploadFilled /></el-icon>
    <p v-if="!selectedFile" class="upload-text">
      Drag and drop audio file here, or click to select
    </p>
    <div v-else class="file-info">
      <p class="file-name">{{ selectedFile.name }}</p>
      <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
    </div>
    <p class="format-hint">
      Supported: {{ ALLOWED_EXTENSIONS.join(', ') }} (max 20MB)
    </p>
  </div>
</template>

<style scoped>
.upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s;
}
.upload-area:hover,
.upload-area.drag-over {
  border-color: #409eff;
}
.upload-icon {
  color: #c0c4cc;
  margin-bottom: 12px;
}
.upload-text {
  color: #606266;
  margin: 8px 0;
}
.file-info {
  margin: 8px 0;
}
.file-name {
  font-weight: bold;
  color: #303133;
}
.file-size {
  color: #909399;
  font-size: 14px;
}
.format-hint {
  color: #909399;
  font-size: 12px;
  margin-top: 8px;
}
</style>
```

- [x] **Step 4: 编写 ModeSelector 测试**

`frontend/src/__tests__/ModeSelector.test.ts`：

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ModeSelector from '@/components/ModeSelector.vue'

describe('ModeSelector', () => {
  it('renders two options', () => {
    const wrapper = mount(ModeSelector)
    expect(wrapper.find('[data-testid="mode-2stems"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="mode-4stems"]').exists()).toBe(true)
  })

  it('defaults to 2-stem mode', () => {
    const wrapper = mount(ModeSelector)
    expect(wrapper.emitted('update:modelValue')).toBeFalsy()
    const radio = wrapper.find('[data-testid="mode-2stems"] input') || wrapper.find('input[value="2stems"]')
    // Default should be 2stems
    expect(wrapper.vm.modelValue ?? '2stems').toBe('2stems')
  })

  it('emits mode-change when selecting 4-stem', async () => {
    const wrapper = mount(ModeSelector, {
      props: { modelValue: '2stems' },
    })
    const radio4 = wrapper.find('[data-testid="mode-4stems"]')
    await radio4.trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })
})
```

- [x] **Step 5: 编写 ModeSelector 组件**

`frontend/src/components/ModeSelector.vue`：

```vue
<script setup lang="ts">
import type { SeparationMode } from '@/types'

const model = defineModel<SeparationMode>({ default: '2stems' })
</script>

<template>
  <div class="mode-selector">
    <h3 class="mode-title">Separation Mode</h3>
    <el-radio-group v-model="model" class="mode-group">
      <el-radio-button data-testid="mode-2stems" value="2stems">
        2 Stems (Vocals + Accompaniment)
      </el-radio-button>
      <el-radio-button data-testid="mode-4stems" value="4stems">
        4 Stems (Vocals + Drums + Bass + Other)
      </el-radio-button>
    </el-radio-group>
  </div>
</template>

<style scoped>
.mode-selector {
  margin: 20px 0;
}
.mode-title {
  margin-bottom: 12px;
  font-size: 16px;
  color: #303133;
}
.mode-group {
  width: 100%;
}
</style>
```

- [x] **Step 6: 运行测试确认通过**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/frontend
npx vitest run src/__tests__/FileUploader.test.ts src/__tests__/ModeSelector.test.ts
```

预期：全部 PASS

- [x] **Step 7: 提交**

```bash
git add frontend/src/components/FileUploader.vue frontend/src/components/ModeSelector.vue frontend/src/__tests__/
git commit -m "feat: add FileUploader and ModeSelector components with validation"
```

---

## Task 12: TaskProgress 和 StemPlayer 组件

**文件：**
- Create: `frontend/src/components/TaskProgress.vue`
- Create: `frontend/src/components/StemPlayer.vue`
- Create: `frontend/src/components/DownloadPanel.vue`
- Create: `frontend/src/__tests__/TaskProgress.test.ts`

- [x] **Step 1: 编写 TaskProgress 测试**

`frontend/src/__tests__/TaskProgress.test.ts`：

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskProgress from '@/components/TaskProgress.vue'

describe('TaskProgress', () => {
  it('shows waiting state for PENDING', () => {
    const wrapper = mount(TaskProgress, {
      props: { status: 'PENDING' },
    })
    expect(wrapper.text()).toContain('Waiting')
  })

  it('shows processing state with progress', () => {
    const wrapper = mount(TaskProgress, {
      props: { status: 'PROCESSING' },
    })
    expect(wrapper.text()).toContain('Processing')
  })

  it('shows completed state', () => {
    const wrapper = mount(TaskProgress, {
      props: { status: 'COMPLETED' },
    })
    expect(wrapper.text()).toContain('Completed')
  })

  it('shows failed state with error message', () => {
    const wrapper = mount(TaskProgress, {
      props: { status: 'FAILED', errorMessage: 'Spleeter inference failed' },
    })
    expect(wrapper.text()).toContain('Failed')
    expect(wrapper.text()).toContain('Spleeter inference failed')
  })

  it('shows network error', () => {
    const wrapper = mount(TaskProgress, {
      props: { status: 'PENDING', networkError: 'Network error, please refresh' },
    })
    expect(wrapper.text()).toContain('Network error')
  })
})
```

- [x] **Step 2: 运行测试确认失败**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/frontend
npx vitest run src/__tests__/TaskProgress.test.ts
```

预期：FAIL — `Cannot find module '@/components/TaskProgress.vue'`

- [x] **Step 3: 编写 TaskProgress 组件**

`frontend/src/components/TaskProgress.vue`：

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { TaskStatus } from '@/types'

const props = defineProps<{
  status: TaskStatus
  errorMessage?: string | null
  networkError?: string | null
}>()

const statusConfig = computed(() => {
  switch (props.status) {
    case 'PENDING':
      return { text: 'Waiting...', type: 'info' as const, icon: 'loading' }
    case 'PROCESSING':
      return { text: 'Processing...', type: 'warning' as const, icon: 'loading' }
    case 'COMPLETED':
      return { text: 'Completed!', type: 'success' as const, icon: 'success' }
    case 'FAILED':
      return { text: 'Failed', type: 'danger' as const, icon: 'error' }
    default:
      return { text: 'Unknown', type: 'info' as const, icon: 'info' }
  }
})
</script>

<template>
  <div class="task-progress">
    <div v-if="networkError" class="network-error">
      <el-alert :title="networkError" type="error" :closable="false" show-icon />
    </div>

    <div v-else class="status-display">
      <el-progress
        v-if="status === 'PENDING' || status === 'PROCESSING'"
        :percentage="status === 'PROCESSING' ? 50 : 10"
        :status="statusConfig.type"
        :indeterminate="status === 'PROCESSING'"
        :stroke-width="20"
        :text-inside="true"
      />
      <el-alert
        v-if="status === 'COMPLETED'"
        title="Separation completed!"
        type="success"
        :closable="false"
        show-icon
      />
      <el-alert
        v-if="status === 'FAILED'"
        :title="`Failed: ${errorMessage || 'Unknown error'}`"
        type="error"
        :closable="false"
        show-icon
      />
      <p class="status-text">{{ statusConfig.text }}</p>
    </div>
  </div>
</template>

<style scoped>
.task-progress {
  margin: 20px 0;
}
.status-text {
  text-align: center;
  margin-top: 8px;
  color: #606266;
}
.network-error {
  margin: 12px 0;
}
</style>
```

- [x] **Step 4: 编写 StemPlayer 组件**

`frontend/src/components/StemPlayer.vue`：

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Download } from '@element-plus/icons-vue'
import { useAudioPlayer } from '@/composables/useAudioPlayer'

const props = defineProps<{
  stemName: string
  streamUrl: string
  downloadUrl: string
}>()

const waveformRef = ref<HTMLElement | null>(null)
const {
  isPlaying,
  currentTime,
  duration,
  isLoading,
  hasError,
  init,
  togglePlay,
} = useAudioPlayer(waveformRef, props.streamUrl)

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

onMounted(init)
</script>

<template>
  <el-card class="stem-player" shadow="hover">
    <template #header>
      <div class="stem-header">
        <span class="stem-name">{{ stemName }}</span>
        <el-button :icon="Download" circle size="small" @click="window.open(downloadUrl)" />
      </div>
    </template>

    <div v-if="isLoading" class="loading-state">
      <el-skeleton :rows="1" animated />
    </div>

    <div v-else-if="hasError" class="error-state">
      <el-alert title="Failed to load audio" type="error" :closable="false" />
    </div>

    <div v-else class="player-content">
      <div ref="waveformRef" class="waveform-container" />
      <div class="player-controls">
        <el-button :type="isPlaying ? 'warning' : 'primary'" @click="togglePlay">
          {{ isPlaying ? 'Pause' : 'Play' }}
        </el-button>
        <span class="time-display">
          {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
        </span>
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.stem-player {
  margin-bottom: 16px;
}
.stem-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.stem-name {
  font-weight: bold;
  text-transform: capitalize;
}
.waveform-container {
  margin: 12px 0;
}
.player-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}
.time-display {
  color: #909399;
  font-family: monospace;
  font-size: 14px;
}
.loading-state,
.error-state {
  padding: 12px 0;
}
</style>
```

- [x] **Step 5: 编写 DownloadPanel 组件**

`frontend/src/components/DownloadPanel.vue`：

```vue
<script setup lang="ts">
import { Download } from '@element-plus/icons-vue'

defineProps<{
  downloadAllUrl: string
}>()
</script>

<template>
  <div class="download-panel">
    <el-button type="success" :icon="Download" size="large" @click="window.open(downloadAllUrl)">
      Download All Stems (ZIP)
    </el-button>
  </div>
</template>

<style scoped>
.download-panel {
  text-align: center;
  margin: 24px 0;
}
</style>
```

- [x] **Step 6: 运行测试确认通过**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/frontend
npx vitest run src/__tests__/TaskProgress.test.ts
```

预期：全部 PASS

- [x] **Step 7: 提交**

```bash
git add frontend/src/components/TaskProgress.vue frontend/src/components/StemPlayer.vue frontend/src/components/DownloadPanel.vue frontend/src/__tests__/TaskProgress.test.ts
git commit -m "feat: add TaskProgress, StemPlayer, and DownloadPanel components"
```

---

## Task 13: 页面视图

**文件：**
- Create: `frontend/src/views/HomeView.vue`
- Create: `frontend/src/views/ResultView.vue`

- [x] **Step 1: 编写 HomeView**

`frontend/src/views/HomeView.vue`：

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import FileUploader from '@/components/FileUploader.vue'
import ModeSelector from '@/components/ModeSelector.vue'
import type { SeparationMode } from '@/types'
import { createTask } from '@/api/client'

const router = useRouter()
const selectedFile = ref<File | null>(null)
const mode = ref<SeparationMode>('2stems')
const isSubmitting = ref(false)

function onFileSelected(file: File) {
  selectedFile.value = file
}

function onFileError(message: string) {
  selectedFile.value = null
}

async function handleSubmit() {
  if (!selectedFile.value) {
    ElMessage.warning('Please select an audio file first')
    return
  }

  isSubmitting.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('mode', mode.value)

    const task = await createTask(formData)
    router.push({ name: 'result', params: { taskId: task.id } })
  } catch (err: any) {
    const errorData = err.response?.data
    if (errorData?.file) {
      ElMessage.error(Array.isArray(errorData.file) ? errorData.file[0] : errorData.file)
    } else if (errorData?.mode) {
      ElMessage.error(Array.isArray(errorData.mode) ? errorData.mode[0] : errorData.mode)
    } else if (errorData?.error) {
      ElMessage.error(errorData.error)
    } else {
      ElMessage.error('Upload failed. Please try again.')
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="home-view">
    <h1 class="title">AI Audio Separator</h1>
    <p class="subtitle">Upload an audio file to separate it into individual stems</p>

    <FileUploader
      @file-selected="onFileSelected"
      @error="onFileError"
    />

    <ModeSelector v-model="mode" />

    <el-button
      type="primary"
      size="large"
      :loading="isSubmitting"
      :disabled="!selectedFile"
      class="submit-btn"
      @click="handleSubmit"
    >
      {{ isSubmitting ? 'Uploading...' : 'Start Separation' }}
    </el-button>
  </div>
</template>

<style scoped>
.home-view {
  padding: 40px 0;
  text-align: center;
}
.title {
  font-size: 32px;
  color: #303133;
  margin-bottom: 8px;
}
.subtitle {
  color: #909399;
  margin-bottom: 32px;
}
.submit-btn {
  margin-top: 24px;
  min-width: 200px;
}
</style>
```

- [x] **Step 2: 编写 ResultView**

`frontend/src/views/ResultView.vue`：

```vue
<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import TaskProgress from '@/components/TaskProgress.vue'
import StemPlayer from '@/components/StemPlayer.vue'
import DownloadPanel from '@/components/DownloadPanel.vue'
import { useTask } from '@/composables/useTask'
import {
  getStemStreamUrl,
  getStemDownloadUrl,
  getDownloadAllUrl,
} from '@/api/client'

const route = useRoute()
const taskId = route.params.taskId as string

const { task, isLoading, error, startPolling } = useTask(taskId)

onMounted(startPolling)

const stemEntries = computed(() => {
  if (!task.value || task.value.status !== 'COMPLETED') return []
  return Object.entries(task.value.stems).map(([name, info]) => ({
    name,
    streamUrl: getStemStreamUrl(taskId, name),
    downloadUrl: getStemDownloadUrl(taskId, name),
  }))
})

const downloadAllUrl = computed(() => getDownloadAllUrl(taskId))
</script>

<template>
  <div class="result-view">
    <h1 class="title">
      {{ task?.original_filename ?? 'Processing...' }}
    </h1>

    <TaskProgress
      v-if="task"
      :status="task.status"
      :error-message="task.error_message"
      :network-error="error"
    />

    <div v-if="task?.status === 'COMPLETED'" class="stems-container">
      <StemPlayer
        v-for="stem in stemEntries"
        :key="stem.name"
        :stem-name="stem.name"
        :stream-url="stem.streamUrl"
        :download-url="stem.downloadUrl"
      />
      <DownloadPanel :download-all-url="downloadAllUrl" />
    </div>

    <div v-if="isLoading && !task" class="loading">
      <el-skeleton :rows="3" animated />
    </div>
  </div>
</template>

<style scoped>
.result-view {
  padding: 40px 0;
}
.title {
  font-size: 24px;
  color: #303133;
  margin-bottom: 24px;
  text-align: center;
}
.stems-container {
  margin-top: 24px;
}
.loading {
  padding: 40px 0;
}
</style>
```

- [x] **Step 3: 验证前端编译**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/frontend
npm run build
```

预期：编译成功，无 TypeScript 错误。

- [x] **Step 4: 提交**

```bash
git add frontend/src/views/ frontend/src/components/
git commit -m "feat: add HomeView and ResultView pages with full user flow"
```

---

## Task 14: 端到端验证

**文件：**
- Modify: `.gitignore`（更新）

- [x] **Step 1: 更新 .gitignore**

在项目根目录 `.gitignore` 中添加：

```
# Backend
backend/db.sqlite3
backend/media/
backend/.pytest_cache/
backend/__pycache__/
backend/**/__pycache__/
*.pyc

# Frontend
frontend/node_modules/
frontend/dist/
frontend/.vite/
```

- [x] **Step 2: 启动后端**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run python manage.py runserver
```

预期：Django 在 `http://localhost:8000` 启动。

- [x] **Step 3: 启动前端（另一个终端）**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/frontend
npm run dev
```

预期：Vite 在 `http://localhost:5173` 启动。

- [x] **Step 4: 手动 E2E 测试**

1. 打开 `http://localhost:5173`
2. 上传一个 MP3 文件（测试用音频文件）
3. 选择 2-stem 模式
4. 点击 "Start Separation"
5. 等待跳转到结果页
6. 启动 Worker：`cd backend && uv run python manage.py run_worker`
7. 观察结果页状态从 "Waiting" 变为 "Processing" 再变为 "Completed"
8. 播放每个音轨的波形
9. 下载单个音轨和全部音轨（ZIP）

- [x] **Step 5: 运行全部后端测试**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/backend
uv run pytest -v --tb=short
```

预期：全部 PASS

- [x] **Step 6: 运行全部前端测试**

```bash
cd /Users/lixueduan/17x/idea/vocalremover/frontend
npx vitest run
```

预期：全部 PASS

- [x] **Step 7: 提交**

```bash
git add .gitignore
git commit -m "chore: update gitignore for backend and frontend"
```

---

## 依赖关系图

```
Task 1 (Django 初始化)
  └─▶ Task 2 (Task 模型)
       └─▶ Task 3 (序列化器)
            └─▶ Task 4 (API 视图 + URL)
                 ├─▶ Task 5 (Spleeter 封装)
                 │    └─▶ Task 6 (Worker)
                 │         └─▶ Task 7 (清理命令)
                 └─▶ Task 8 (Admin)

Task 9 (Vue 初始化)
  └─▶ Task 10 (API 客户端 + Composables)
       └─▶ Task 11 (FileUploader + ModeSelector)
            └─▶ Task 12 (TaskProgress + StemPlayer)
                 └─▶ Task 13 (页面视图)

Task 14 (端到端验证) — 依赖全部前置任务
```

后端 Task 1-8 和前端 Task 9-13 可以在 Task 4 和 Task 10 完成后并行推进。
