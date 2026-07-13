from django.db import models


class UploadedDocument(models.Model):

    filename = models.CharField(
        max_length=255
    )

    extracted_text = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.filename