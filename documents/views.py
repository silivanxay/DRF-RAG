import os
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.conf import settings
from drf_spectacular.utils import extend_schema

from .models import Document
from .serializers import DocumentSerializer, IngestSerializer
from .tasks import ingest_document


class IngestView(APIView):
    parser_classes = [MultiPartParser]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                        "description": "PDF file to ingest",
                    },
                    "collection_name": {
                        "type": "string",
                        "default": "documents",
                        "description": "Qdrant collection to store embeddings in",
                    },
                },
                "required": ["file"],
            }
        },
        responses={202: DocumentSerializer},
        summary="Upload and ingest a PDF",
        description="Upload a PDF file. A Celery task will chunk, embed, and store it in Qdrant.",
    )
    def post(self, request):
        serializer = IngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        collection_name = serializer.validated_data["collection_name"]

        # Save file to media/uploads/
        upload_dir = settings.MEDIA_ROOT / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / uploaded_file.name

        with open(file_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # Create DB record
        doc = Document.objects.create(
            filename=uploaded_file.name,
            file_path=str(file_path),
            collection_name=collection_name,
        )

        # Dispatch Celery task
        ingest_document.delay(doc.id, str(file_path), collection_name)

        return Response(DocumentSerializer(doc).data, status=status.HTTP_202_ACCEPTED)


class DocumentListView(ListAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class DocumentDetailView(RetrieveAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
