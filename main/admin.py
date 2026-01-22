from django.contrib import admin
from .models import UploadLog

@admin.register(UploadLog)
class UploadLogAdmin(admin.ModelAdmin):
    list_display = ("filename", "user", "uploaded_at", "rows_added", "rows_updated")
    list_filter = ("user", "uploaded_at")
