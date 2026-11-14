from django import forms
from apps.grades.forms import TailwindFormMixin
from .models import Attendance


class AttendanceForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["student", "subject", "type", "date", "justified", "reason"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}