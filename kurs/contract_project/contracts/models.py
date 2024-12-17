# contracts/models.py

from django.db import models
from docx import Document

class Contract(models.Model):
    full_name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=50)
    date = models.DateField()
    signed_document = models.FileField(upload_to='signed_contracts/')

    class Meta:
        app_label = 'contracts'  # Явно указываем приложение

    def __str__(self):
        return f"Contract for {self.full_name}"

