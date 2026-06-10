from django.db import models


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    collection_name = models.CharField(max_length=100, default="documents")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    chunk_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.filename} [{self.status}]"
