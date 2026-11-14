from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Enrollment


class EnrollmentForm(forms.ModelForm):
    """Formulaire pour Enrollment."""

    class Meta:
        model = Enrollment
        fields = ['student', 'classroom', 'academic_year', 'statut']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'classroom': forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)

        from apps.students.models import Student
        from apps.classes.models import ClassRoom
        from apps.schools.models import AcademicYear

        if school:
            self.fields['student'].queryset = Student.objects.filter(school=school, is_active=True)
            self.fields['classroom'].queryset = ClassRoom.objects.filter(school=school, is_active=True)
            self.fields['academic_year'].queryset = AcademicYear.objects.filter(school=school, is_active=True)
        else:
            self.fields['student'].queryset = Student.objects.filter(is_active=True)
            self.fields['classroom'].queryset = ClassRoom.objects.filter(is_active=True)
            self.fields['academic_year'].queryset = AcademicYear.objects.filter(is_active=True)

        self.fields['student'].label_from_instance = lambda obj: f"{obj.user.get_full_name() or obj.username} ({obj.matricule})"
        self.fields['classroom'].label_from_instance = lambda obj: f"{obj.nom} ({obj.academic_year.nom})"
        self.fields['academic_year'].label_from_instance = lambda obj: f"{obj.nom} ({obj.school.nom})"


class EnrollmentSearchForm(forms.Form):
    """Formulaire de recherche pour les inscriptions."""
    q = forms.CharField(
        required=False,
        label=_('Recherche'),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Élève, classe, numéro inscription...'
        })
    )
    academic_year = forms.ModelChoiceField(
        required=False,
        queryset=None,
        label=_('Année scolaire'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    classroom = forms.ModelChoiceField(
        required=False,
        queryset=None,
        label=_('Classe'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    statut = forms.ChoiceField(
        required=False,
        choices=[('', _('Tous'))] + list(Enrollment.Statut.choices),
        label=_('Statut'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)

        from apps.schools.models import AcademicYear
        from apps.classes.models import ClassRoom

        if school:
            self.fields['academic_year'].queryset = AcademicYear.objects.filter(school=school, is_active=True)
            self.fields['classroom'].queryset = ClassRoom.objects.filter(school=school, is_active=True)
        else:
            self.fields['academic_year'].queryset = AcademicYear.objects.filter(is_active=True)
            self.fields['classroom'].queryset = ClassRoom.objects.filter(is_active=True)