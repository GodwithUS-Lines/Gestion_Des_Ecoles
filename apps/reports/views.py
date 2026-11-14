from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView

from apps.grades.mixins import StaffRequiredMixin
from apps.grades.models import Grade, Period
from apps.students.models import Student
from .models import ReportCard
from .services import generate_report_cards, subject_average


class ReportCardListView(StaffRequiredMixin, ListView):
    model = ReportCard
    template_name = "reports/reportcard_list.html"
    extra_context = {"page_title": "Bulletins"}

    def get_queryset(self):
        qs = ReportCard.objects.select_related("student", "period")
        period = self.request.GET.get("period")
        return qs.filter(period_id=period) if period else qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["periods"] = Period.objects.all()
        ctx["selected_period"] = self.request.GET.get("period", "")
        return ctx


class GenerateReportCardsView(StaffRequiredMixin, View):
    def post(self, request):
        period = get_object_or_404(Period, pk=request.POST.get("period"))
        # TODO: filtrer par classe via apps.enrollments quand le modèle sera prêt
        cards = generate_report_cards(Student.objects.all(), period)
        messages.success(request, f"{len(cards)} bulletin(s) généré(s) pour {period}.")
        return redirect(f"/reports/?period={period.pk}")


class ReportCardDetailView(StaffRequiredMixin, DetailView):
    model = ReportCard
    template_name = "reports/reportcard_detail.html"
    extra_context = {"page_title": "Bulletin"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        card = self.object
        subject_ids = (Grade.objects.filter(student=card.student, period=card.period)
                       .values_list("subject_id", flat=True).distinct())
        rows = []
        for g in Grade.objects.filter(student=card.student, period=card.period).select_related("subject"):
            if g.subject_id in subject_ids and g.subject_id not in [r["subject"].pk for r in rows]:
                rows.append({
                    "subject": g.subject,
                    "average": subject_average(card.student, g.subject, card.period),
                })
        ctx["rows"] = rows
        return ctx