from django.contrib import admin

from.models import SchoolClass


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("name","school","level","academic_year","capacity","is_active")
    list_filter = ("school","academic_year","is_active")
    search_fields = ("name","level")
