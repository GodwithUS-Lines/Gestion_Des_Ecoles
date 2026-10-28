from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Period(models.Model):
    name = models.CharField(max_length=50)          # ex: Trimestre 1
    start_date = models.DateField()
    end_date = models.DateField()
    school_year = models.CharField(max_length=9)    # ex: 2025-2026

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.school_year})"


class Grade(models.Model):
    TYPES = [("HW", "Devoir"), ("QZ", "Interrogation"), ("EX", "Composition")]

    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="grades")
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE, related_name="grades")
    period = models.ForeignKey(Period, on_delete=models.CASCADE, related_name="grades")
    evaluation_type = models.CharField(max_length=2, choices=TYPES, default="HW")
    value = models.DecimalField(
        max_digits=4, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
    )
    coefficient = models.PositiveSmallIntegerField(default=1)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.student} - {self.subject} : {self.value}/20"