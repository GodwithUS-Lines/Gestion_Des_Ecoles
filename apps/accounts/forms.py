from django import forms
from django.contrib.auth.forms import (
    UserCreationForm, UserChangeForm, AuthenticationForm,
    PasswordChangeForm, PasswordResetForm, SetPasswordForm
)
from django.utils.translation import gettext_lazy as _

from .models import User, Role


class UserRegistrationForm(UserCreationForm):
    """Formulaire d'inscription (si inscription publique autorisée)."""

    email = forms.EmailField(
        label=_('Email'),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'email@exemple.com'})
    )
    role = forms.ChoiceField(
        label=_('Rôle'),
        choices=Role.choices,
        initial=Role.STUDENT,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    first_name = forms.CharField(
        label=_('Prénom'),
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Prénom'})
    )
    last_name = forms.CharField(
        label=_('Nom'),
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom'})
    )
    telephone = forms.CharField(
        label=_('Téléphone'),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+229 XX XX XX XX'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'first_name', 'last_name', 'telephone', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'nom_utilisateur'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Cet email est déjà utilisé.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.telephone = self.cleaned_data['telephone']
        if commit:
            user.save()
        return user


class UserProfileForm(UserChangeForm):
    """Formulaire de modification du profil utilisateur."""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'telephone', 'adresse', 'date_naissance', 'photo')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'telephone': forms.TextInput(attrs={'class': 'form-input'}),
            'adresse': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'photo': forms.FileInput(attrs={'class': 'form-file'}),
        }


class CustomAuthenticationForm(AuthenticationForm):
    """Formulaire de connexion personnalisé avec Tailwind."""

    username = forms.CharField(
        label=_('Email ou nom d\'utilisateur'),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email ou nom d\'utilisateur',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label=_('Mot de passe'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Mot de passe',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Permettre la connexion par email OU username
        self.fields['username'].label = _('Email ou nom d\'utilisateur')


class CustomPasswordChangeForm(PasswordChangeForm):
    """Formulaire de changement de mot de passe."""

    old_password = forms.CharField(
        label=_('Ancien mot de passe'),
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Ancien mot de passe'})
    )
    new_password1 = forms.CharField(
        label=_('Nouveau mot de passe'),
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Nouveau mot de passe'})
    )
    new_password2 = forms.CharField(
        label=_('Confirmer le nouveau mot de passe'),
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirmer le nouveau mot de passe'})
    )


class CustomPasswordResetForm(PasswordResetForm):
    """Formulaire de demande de réinitialisation."""

    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'votre@email.com'})
    )


class CustomSetPasswordForm(SetPasswordForm):
    """Formulaire de définition du nouveau mot de passe."""

    new_password1 = forms.CharField(
        label=_('Nouveau mot de passe'),
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Nouveau mot de passe'})
    )
    new_password2 = forms.CharField(
        label=_('Confirmer le nouveau mot de passe'),
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirmer le nouveau mot de passe'})
    )