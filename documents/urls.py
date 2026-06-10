from django.urls import path
from .views import IngestView, DocumentListView, DocumentDetailView

urlpatterns = [
    path("ingest/", IngestView.as_view(), name="ingest"),
    path("documents/", DocumentListView.as_view(), name="document-list"),
    path("documents/<int:pk>/", DocumentDetailView.as_view(), name="document-detail"),
]
