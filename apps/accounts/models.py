from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class Role(models.TextChoices):
    """Rôles utilisateurs selon spécifications (RG20, D3 ERD)."""
    ADMIN = 'ADMIN', _('Administrateur')
    DIRECTOR = 'DIRECTOR', _('Directeur / Responsable')
    TEACHER = 'TEACHER', _('Enseignant')
    STUDENT = 'STUDENT', _('Élève')
    PARENT = 'PARENT', _('Parent / Tuteur')
    ACCOUNTANT = 'ACCOUNTANT', _('Comptable / Caissier')


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé.
    Hérite d'AbstractUser pour conserver username, email, password, is_staff, is_superuser, etc.
    Champs ajoutés selon cahier des charges.
    """

    email = models.EmailField(_('adresse email'), unique=True)
    role = models.CharField(
        _('rôle'),
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text=_('Rôle déterminant les permissions dans l\'application')
    )
    telephone = models.CharField(
        _('téléphone'),
        max_length=20,
        blank=True,
        default=''
    )
    adresse = models.TextField(
        _('adresse'),
        blank=True,
        default=''
    )
    date_naissance = models.DateField(
        _('date de naissance'),
        null=True,
        blank=True
    )
    photo = models.ImageField(
        _('photo de profil'),
        upload_to='users/photos/',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        _('actif'),
        default=True,
        help_text=_('Désactiver au lieu de supprimer (RG19)')
    )
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)

    # Utiliser l'email comme identifiant unique pour l'authentification
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'role']

    objects = UserManager()

    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def clean(self):
        super().clean()
        self.email = self.email.lower().strip()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # Propriétés de commodité pour vérification de rôles
    @property
    def is_admin(self):
        return self.role == Role.ADMIN or self.is_superuser

    @property
    def is_director(self):
        return self.role == Role.DIRECTOR

    @property
    def is_teacher(self):
        return self.role == Role.TEACHER

    @property
    def is_student(self):
        return self.role == Role.STUDENT

    @property
    def is_parent(self):
        return self.role == Role.PARENT

    @property
    def is_accountant(self):
        return self.role == Role.ACCOUNTANT

    def has_permission(self, permission_codename):
        """Vérifie une permission Django standard."""
        return self.has_perm(permission_codename)

    def get_dashboard_url(self):
        """Redirection selon le rôle après connexion."""
        dashboards = {
            Role.ADMIN: 'admin:index',
            Role.DIRECTOR: 'dashboard',
            Role.TEACHER: 'dashboard',
            Role.STUDENT: 'dashboard',
            Role.PARENT: 'dashboard',
            Role.ACCOUNTANT: 'dashboard',
        }
        return dashboards.get(self.role, 'dashboard')