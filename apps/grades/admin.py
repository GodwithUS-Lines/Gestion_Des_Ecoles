from django.contrib import admin
from .models import Period, Grade

admin.site.register(Period)


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "period", "evaluation_type", "value", "date")
    list_filter = ("period", "subject", "evaluation_type")