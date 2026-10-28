from django.db import models



class ReportCard(models.Model):
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="report_cards")
    period = models.ForeignKey("grades.Period", on_delete=models.CASCADE)
    overall_average = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    rank = models.PositiveIntegerField(null=True, blank=True)
    absences_count = models.PositiveIntegerField(default=0)
    comment = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "period")

    def __str__(self):
        return f"Bulletin {self.student} - {self.period}"
# Create your models here.
