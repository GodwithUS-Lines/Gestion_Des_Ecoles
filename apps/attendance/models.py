from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Attendance(models.Model):
    TYPES = [("ABS", "Absence"), ("LATE", "Retard")]

    student = models.ForeignKey("students.Student", on_delete=models.CASCADE,
                                related_name="attendances", verbose_name=_("élève"))
    subject = models.ForeignKey("subjects.Subject", on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name=_("matière"))
    type = models.CharField(_("type"), max_length=4, choices=TYPES, default="ABS")
    date = models.DateField(_("date"))
    justified = models.BooleanField(_("justifiée"), default=False)
    reason = models.CharField(_("motif"), max_length=255, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, verbose_name=_("saisie par"))

    class Meta:
        ordering = ["-date"]
        verbose_name = _("absence / retard")
        verbose_name_plural = _("absences et retards")

    def __str__(self):
        return f"{self.student} - {self.get_type_display()} le {self.date}"