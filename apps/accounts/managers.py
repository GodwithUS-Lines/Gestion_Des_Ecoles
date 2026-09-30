from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager pour le modèle User personnalisé (email comme USERNAME_FIELD)."""

    def create_user(self, email, username, role, password=None, **extra_fields):
        if not email:
            raise ValueError(_('L\'email est obligatoire'))
        if not username:
            raise ValueError(_('Le nom d\'utilisateur est obligatoire'))
        if not role:
            raise ValueError(_('Le rôle est obligatoire'))

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('role', 'ADMIN')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('role') != 'ADMIN':
            raise ValueError(_('Un superutilisateur doit avoir le rôle ADMIN'))
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Un superutilisateur doit avoir is_staff=True'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Un superutilisateur doit avoir is_superuser=True'))

        return self.create_user(email, username, password=password, **extra_fields)