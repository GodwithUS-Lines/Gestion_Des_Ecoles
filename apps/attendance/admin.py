from django.contrib import admin

from django.contrib import admin
from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "type", "date", "subject", "justified")
    list_filter = ("type", "justified", "date")

# Register your models here.
