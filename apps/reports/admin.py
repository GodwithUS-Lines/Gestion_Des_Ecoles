from django.contrib import admin

from django.contrib import admin
from .models import ReportCard


@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display = ("student", "period", "overall_average", "rank", "absences_count")
    list_filter = ("period",)

# Register your models here.
