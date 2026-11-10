from django.db import models

from django.db import models


class Subject(models.Model):
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="subjects",
        verbose_name="Ecoles",
)
name = models.CharField("Nom",max_length=100)
code = models.CharField("Code",max_length=20)
coefficient = models.PositiveIntegerField("Coefficient",default=1)
is_active = models.BooleanField("Active",default=True)

class Meta:
    verbose_name = "Matière"
    verbose_name_plural = "Matières"
    ordering = ["school","name"]
    unique_together = ("school","code")

    def __str__(self):
        return f"{self.name}({self.code})"
