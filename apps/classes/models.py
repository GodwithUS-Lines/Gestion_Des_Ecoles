from django.db import models


class SchoolClass(models.Model):
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="classes",
        verbose_name="Ecole",
    )
    name = models.CharField("Nom",max_length=100)
    level = models.CharField("Niveau",max_length=50,blank=True)
    academic_year = models.CharField("Année scolaire",max_length=9)
    capacity = models.PositiveIntegerField("Capacité",default=40)
    is_active = models.BooleanField("Active",default=True)

    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        ordering = ["school","name"]
        unique_together = ("school","name","academic_year")

        def __str__(self):
            return f"{self.name} ({self.academic_year})"
