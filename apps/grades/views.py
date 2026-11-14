from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .forms import GradeForm
from .mixins import StaffRequiredMixin
from .models import Grade, Period

LIST_URL = reverse_lazy("grades:list")


class GradeListView(StaffRequiredMixin, ListView):
    model = Grade
    template_name = "grades/grade_list.html"
    paginate_by = 20
    extra_context = {"page_title": "Notes"}

    def get_queryset(self):
        qs = Grade.objects.select_related("student", "subject", "period")
        period = self.request.GET.get("period")
        return qs.filter(period_id=period) if period else qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["periods"] = Period.objects.all()
        ctx["selected_period"] = self.request.GET.get("period", "")
        return ctx


class GradeCreateView(StaffRequiredMixin, CreateView):
    model = Grade
    form_class = GradeForm
    template_name = "crud/form.html"
    success_url = LIST_URL
    extra_context = {"page_title": "Ajouter une note", "cancel_url": LIST_URL}

    def form_valid(self, form):
        messages.success(self.request, "Note enregistrée.")
        return super().form_valid(form)


class GradeUpdateView(StaffRequiredMixin, UpdateView):
    model = Grade
    form_class = GradeForm
    template_name = "crud/form.html"
    success_url = LIST_URL
    extra_context = {"page_title": "Modifier la note", "cancel_url": LIST_URL}

    def form_valid(self, form):
        messages.success(self.request, "Note modifiée.")
        return super().form_valid(form)


class GradeDeleteView(StaffRequiredMixin, DeleteView):
    model = Grade
    template_name = "crud/confirm_delete.html"
    success_url = LIST_URL
    extra_context = {"cancel_url": LIST_URL}

    def form_valid(self, form):
        messages.success(self.request, "Note supprimée.")
        return super().form_valid(form)