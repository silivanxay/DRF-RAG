from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("filename", "collection_name", "status", "chunk_count", "created_at")
    list_filter = ("status", "collection_name")
    search_fields = ("filename",)
    readonly_fields = ("file_path", "chunk_count", "error_message", "created_at", "updated_at")
