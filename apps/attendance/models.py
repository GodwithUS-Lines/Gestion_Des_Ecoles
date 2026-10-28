from django.db import models

from django.db import models
from django.conf import settings


class Attendance(models.Model):
    TYPES = [("ABS", "Absence"), ("LATE", "Retard")]

    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="attendances")
    subject = models.ForeignKey("subjects.Subject", on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=4, choices=TYPES, default="ABS")
    date = models.DateField()
    justified = models.BooleanField(default=False)
    reason = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.student} - {self.get_type_display()} le {self.date}"

# Create your models here.
