from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import School, AcademicYear


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    """Administration des établissements."""

    list_display = [
        'nom', 'code', 'email', 'telephone',
        'directeur_nom', 'is_active', 'date_creation'
    ]
    list_filter = ['is_active', 'date_creation']
    search_fields = ['nom', 'code', 'email', 'telephone', 'directeur_nom', 'adresse']
    ordering = ['nom']
    readonly_fields = ['date_creation', 'date_modification']

    fieldsets = (
        (None, {
            'fields': ('nom', 'code', 'logo')
        }),
        (_('Coordonnées'), {
            'fields': ('adresse', 'telephone', 'email')
        }),
        (_('Direction'), {
            'fields': ('directeur_nom',)
        }),
        (_('Statut'), {
            'fields': ('is_active',)
        }),
        (_('Dates'), {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    """Administration des années scolaires."""

    list_display = [
        'nom', 'school', 'date_debut', 'date_fin',
        'is_current', 'is_active', 'date_creation'
    ]
    list_filter = ['school', 'is_current', 'is_active', 'date_creation']
    search_fields = ['nom', 'school__nom', 'school__code']
    ordering = ['-date_debut']
    readonly_fields = ['date_creation', 'date_modification']
    list_select_related = ['school']

    fieldsets = (
        (None, {
            'fields': ('school', 'nom')
        }),
        (_('Période'), {
            'fields': ('date_debut', 'date_fin')
        }),
        (_('Statut'), {
            'fields': ('is_current', 'is_active'),
            'description': _('RG01 : Une seule année courante par établissement.')
        }),
        (_('Dates'), {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('school')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'school':
            kwargs['queryset'] = School.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)