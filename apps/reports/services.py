from decimal import Decimal
from django.db.models import Sum, F
from apps.grades.models import Grade
from apps.attendance.models import Attendance
from .models import ReportCard


def subject_average(student, subject, period):
    """Moyenne pondérée d'un élève dans une matière pour une période."""
    qs = Grade.objects.filter(student=student, subject=subject, period=period)
    total_coef = qs.aggregate(s=Sum("coefficient"))["s"]
    if not total_coef:
        return None
    total = qs.aggregate(s=Sum(F("value") * F("coefficient")))["s"]
    return (total / total_coef).quantize(Decimal("0.01"))


def overall_average(student, period):
    """Moyenne générale = moyenne des moyennes par matière."""
    subjects = {
        g.subject
        for g in Grade.objects.filter(student=student, period=period).select_related("subject")
    }
    avgs = [a for a in (subject_average(student, s, period) for s in subjects) if a is not None]
    if not avgs:
        return None
    return (sum(avgs) / len(avgs)).quantize(Decimal("0.01"))


def generate_report_cards(students, period):
    """students = queryset ou liste d'élèves (ex: ceux d'une classe)."""
    cards = []
    for student in students:
        card, _ = ReportCard.objects.get_or_create(student=student, period=period)
        card.overall_average = overall_average(student, period)
        card.absences_count = Attendance.objects.filter(
            student=student, type="ABS",
            date__range=(period.start_date, period.end_date),
        ).count()
        card.save()
        cards.append(card)

    ranked = sorted(
        (c for c in cards if c.overall_average is not None),
        key=lambda c: c.overall_average, reverse=True,
    )
    for rank, c in enumerate(ranked, start=1):
        c.rank = rank
        c.save(update_fields=["rank"])
    return cards