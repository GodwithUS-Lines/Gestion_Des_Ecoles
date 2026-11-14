from django.db import models
from django.utils.translation import gettext_lazy as _


class ReportCard(models.Model):
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE,
                                related_name="report_cards", verbose_name=_("élève"))
    period = models.ForeignKey("grades.Period", on_delete=models.CASCADE,
                               verbose_name=_("période"))
    overall_average = models.DecimalField(_("moyenne générale"), max_digits=4,
                                          decimal_places=2, null=True, blank=True)
    rank = models.PositiveIntegerField(_("rang"), null=True, blank=True)
    absences_count = models.PositiveIntegerField(_("nombre d'absences"), default=0)
    comment = models.TextField(_("appréciation"), blank=True)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "period")
        verbose_name = _("bulletin")
        verbose_name_plural = _("bulletins")

    def __str__(self):
        return f"Bulletin {self.student} - {self.period}"