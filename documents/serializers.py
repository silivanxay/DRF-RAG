from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "filename",
            "collection_name",
            "status",
            "chunk_count",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class IngestSerializer(serializers.Serializer):
    file = serializers.FileField()
    collection_name = serializers.CharField(max_length=100, default="documents")
