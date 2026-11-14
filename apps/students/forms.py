from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Parent, Student


class ParentForm(forms.ModelForm):
    """Formulaire pour Parent."""

    class Meta:
        model = Parent
        fields = ['user', 'profession', 'revenu_mensuel']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'profession': forms.TextInput(attrs={'class': 'form-input'}),
            'revenu_mensuel': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les utilisateurs avec rôle PARENT
        from apps.accounts.models import User, Role
        self.fields['user'].queryset = User.objects.filter(role=Role.PARENT, is_active=True)
        self.fields['user'].label_from_instance = lambda obj: f"{obj.get_full_name() or obj.username} ({obj.email})"


class StudentForm(forms.ModelForm):
    """Formulaire pour Student."""

    class Meta:
        model = Student
        fields = ['user', 'school', 'sexe', 'lieu_naissance', 'nationalite', 'parent']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'school': forms.Select(attrs={'class': 'form-select'}),
            'sexe': forms.Select(attrs={'class': 'form-select'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-input'}),
            'nationalite': forms.TextInput(attrs={'class': 'form-input'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.accounts.models import User, Role
        from apps.schools.models import School
        from .models import Parent

        self.fields['user'].queryset = User.objects.filter(role=Role.STUDENT, is_active=True)
        self.fields['user'].label_from_instance = lambda obj: f"{obj.get_full_name() or obj.username} ({obj.email})"
        self.fields['school'].queryset = School.objects.filter(is_active=True)
        self.fields['parent'].queryset = Parent.objects.filter(is_active=True)
        self.fields['parent'].label_from_instance = lambda obj: f"{obj.user.get_full_name() or obj.user.username}"


class StudentSearchForm(forms.Form):
    """Formulaire de recherche pour les élèves."""
    q = forms.CharField(
        required=False,
        label=_('Recherche'),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nom, prénom, matricule...'
        })
    )
    school = forms.ModelChoiceField(
        required=False,
        queryset=None,
        label=_('Établissement'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.ChoiceField(
        required=False,
        choices=[('', _('Tous')), ('True', _('Actifs')), ('False', _('Inactifs'))],
        label=_('Statut'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.schools.models import School
        self.fields['school'].queryset = School.objects.filter(is_active=True)