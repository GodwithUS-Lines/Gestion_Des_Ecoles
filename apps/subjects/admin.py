from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Administration des matières."""

    list_display = [
        'nom', 'code', 'school', 'niveau', 'serie',
        'coefficient', 'enseignant_responsable', 'is_active'
    ]
    list_filter = [
        'school', 'niveau', 'serie', 'is_active',
        'enseignant_responsable'
    ]
    search_fields = ['nom', 'code', 'school__nom']
    ordering = ['school', 'niveau', 'nom']
    readonly_fields = ['date_creation', 'date_modification']
    list_select_related = ['school', 'serie', 'enseignant_responsable', 'enseignant_responsable__user']

    fieldsets = (
        (None, {
            'fields': ('school', 'nom', 'code')
        }),
        (_('Configuration pédagogique'), {
            'fields': ('niveau', 'serie', 'coefficient'),
            'description': _('Série optionnelle pour 1ère/Terminale. Aucune série pour collège et 2nde.')
        }),
        (_('Encadrement'), {
            'fields': ('enseignant_responsable',)
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
        return super().get_queryset(request).select_related(
            'school', 'serie', 'enseignant_responsable', 'enseignant_responsable__user'
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'school':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        elif db_field.name == 'serie':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        elif db_field.name == 'enseignant_responsable':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)