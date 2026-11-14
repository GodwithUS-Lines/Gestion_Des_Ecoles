from django import forms
from .models import Grade

INPUT_CLASS = "w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"


class TailwindFormMixin:
    """Ajoute les classes Tailwind à tous les champs."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = INPUT_CLASS


class GradeForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Grade
        fields = ["student", "subject", "period", "evaluation_type", "value", "coefficient", "date"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}