from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class Period(models.Model):
    name = models.CharField(_("nom"), max_length=50)
    start_date = models.DateField(_("date de début"))
    end_date = models.DateField(_("date de fin"))
    school_year = models.CharField(_("année scolaire"), max_length=9)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = _("période")
        verbose_name_plural = _("périodes")

    def __str__(self):
        return f"{self.name} ({self.school_year})"


class Grade(models.Model):
    TYPES = [("HW", "Devoir"), ("QZ", "Interrogation"), ("EX", "Composition")]

    student = models.ForeignKey("students.Student", on_delete=models.CASCADE,
                                related_name="grades", verbose_name=_("élève"))
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE,
                                related_name="grades", verbose_name=_("matière"))
    period = models.ForeignKey(Period, on_delete=models.CASCADE,
                               related_name="grades", verbose_name=_("période"))
    evaluation_type = models.CharField(_("type d'évaluation"), max_length=2,
                                       choices=TYPES, default="HW")
    value = models.DecimalField(_("note"), max_digits=4, decimal_places=2,
                                validators=[MinValueValidator(0), MaxValueValidator(20)])
    coefficient = models.PositiveSmallIntegerField(_("coefficient"), default=1)
    date = models.DateField(_("date"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = _("note")
        verbose_name_plural = _("notes")

    def __str__(self):
        return f"{self.student} - {self.subject} : {self.value}/20"