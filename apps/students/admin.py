from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Parent, Student


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    """Administration des parents / tuteurs."""

    list_display = [
        'user', 'profession', 'revenu_mensuel',
        'enfants_count', 'is_active', 'date_creation'
    ]
    list_filter = ['is_active', 'date_creation']
    search_fields = [
        'user__first_name', 'user__last_name', 'user__email',
        'profession'
    ]
    ordering = ['user__last_name', 'user__first_name']
    readonly_fields = ['date_creation', 'date_modification']
    list_select_related = ['user']

    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        (_('Informations professionnelles'), {
            'fields': ('profession', 'revenu_mensuel')
        }),
        (_('Statut'), {
            'fields': ('is_active',)
        }),
        (_('Dates'), {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(role='PARENT', is_active=True))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def enfants_count(self, obj):
        return obj.enfants.filter(is_active=True).count()
    enfants_count.short_description = _('Nb enfants')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Administration des élèves."""

    list_display = [
        'user', 'matricule', 'school', 'sexe',
        'parent', 'is_active', 'date_creation'
    ]
    list_filter = [
        'school', 'sexe', 'is_active', 'date_creation'
    ]
    search_fields = [
        'user__first_name', 'user__last_name', 'user__email',
        'matricule', 'lieu_naissance', 'nationalite'
    ]
    ordering = ['school', 'matricule']
    readonly_fields = ['date_creation', 'date_modification', 'matricule']
    list_select_related = ['user', 'school', 'parent', 'parent__user']

    fieldsets = (
        (None, {
            'fields': ('user', 'school', 'matricule')
        }),
        (_('Informations personnelles'), {
            'fields': ('sexe', 'lieu_naissance', 'nationalite')
        }),
        (_('Famille'), {
            'fields': ('parent',)
        }),
        (_('Statut'), {
            'fields': ('is_active',)
        }),
        (_('Dates'), {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'school', 'parent', 'parent__user')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'school':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        elif db_field.name == 'user':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(role='STUDENT', is_active=True))
        elif db_field.name == 'parent':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)