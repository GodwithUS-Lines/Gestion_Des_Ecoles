from django.contrib import admin

from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("__str__","school","employee_number","is_active")
    list_filter = ("school","is_active")
    search_fields = ("user__last_name","user__first_name","employee_number")
    filter_horizontal = ("subjects","classes")
