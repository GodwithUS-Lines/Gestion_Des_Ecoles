from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Administration du modèle User personnalisé."""

    list_display = [
        'username', 'email', 'get_full_name', 'role',
        'is_active', 'is_staff', 'date_creation'
    ]
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser', 'date_creation']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'telephone']
    ordering = ['-date_creation']
    readonly_fields = ['date_creation', 'date_modification', 'last_login']

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Informations personnelles'), {
            'fields': ('first_name', 'last_name', 'telephone', 'adresse', 'date_naissance', 'photo')
        }),
        (_('Rôle et permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Dates importantes'), {
            'fields': ('last_login', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2'),
        }),
        (_('Informations personnelles'), {
            'fields': ('first_name', 'last_name', 'telephone', 'adresse', 'date_naissance'),
        }),
    )

    def get_full_name(self, obj):
        return obj.get_full_name() or '-'
    get_full_name.short_description = _('Nom complet')