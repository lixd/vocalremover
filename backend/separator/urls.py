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
