from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from apps.grades.mixins import StaffRequiredMixin
from .forms import AttendanceForm
from .models import Attendance

LIST_URL = reverse_lazy("attendance:list")


class AttendanceListView(StaffRequiredMixin, ListView):
    model = Attendance
    template_name = "attendance/attendance_list.html"
    paginate_by = 20
    extra_context = {"page_title": "Absences et retards"}

    def get_queryset(self):
        return Attendance.objects.select_related("student", "subject")


class AttendanceCreateView(StaffRequiredMixin, CreateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = "crud/form.html"
    success_url = LIST_URL
    extra_context = {"page_title": "Enregistrer une absence", "cancel_url": LIST_URL}

    def form_valid(self, form):
        form.instance.recorded_by = self.request.user
        messages.success(self.request, "Absence enregistrée.")
        return super().form_valid(form)


class AttendanceUpdateView(StaffRequiredMixin, UpdateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = "crud/form.html"
    success_url = LIST_URL
    extra_context = {"page_title": "Modifier l'absence", "cancel_url": LIST_URL}

    def form_valid(self, form):
        messages.success(self.request, "Absence modifiée.")
        return super().form_valid(form)


class AttendanceDeleteView(StaffRequiredMixin, DeleteView):
    model = Attendance
    template_name = "crud/confirm_delete.html"
    success_url = LIST_URL
    extra_context = {"cancel_url": LIST_URL}

    def form_valid(self, form):
        messages.success(self.request, "Absence supprimée.")
        return super().form_valid(form)