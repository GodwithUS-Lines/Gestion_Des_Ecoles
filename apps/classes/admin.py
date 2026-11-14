from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Serie, ClassRoom


@admin.register(Serie)
class SerieAdmin(admin.ModelAdmin):
    """Administration des séries."""

    list_display = [
        'code', 'nom', 'niveaux_concernes', 'is_active', 'date_creation'
    ]
    list_filter = ['is_active', 'date_creation']
    search_fields = ['code', 'nom']
    ordering = ['code']
    readonly_fields = ['date_creation', 'date_modification']

    fieldsets = (
        (None, {
            'fields': ('code', 'nom')
        }),
        (_('Configuration'), {
            'fields': ('niveaux_concernes', 'is_active'),
            'description': _('Pour le MVP: niveaux concernés = ["1ere", "terminale"]')
        }),
        (_('Dates'), {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    """Administration des classes."""

    list_display = [
        'nom', 'school', 'academic_year', 'niveau', 'serie',
        'capacite', 'effectif_actuel', 'places_disponibles',
        'professeur_principal', 'is_active'
    ]
    list_filter = [
        'school', 'academic_year', 'niveau', 'serie',
        'is_active', 'professeur_principal'
    ]
    search_fields = ['nom', 'school__nom', 'academic_year__nom']
    ordering = ['school', 'academic_year', 'niveau', 'nom']
    readonly_fields = ['date_creation', 'date_modification', 'effectif_actuel', 'places_disponibles']
    list_select_related = ['school', 'academic_year', 'serie', 'professeur_principal', 'professeur_principal__user']

    fieldsets = (
        (None, {
            'fields': ('school', 'academic_year', 'nom')
        }),
        (_('Niveau et série'), {
            'fields': ('niveau', 'serie'),
            'description': _('Série obligatoire pour 1ère/Terminale. Aucune série pour le collège (6ème-3ème).')
        }),
        (_('Effectifs'), {
            'fields': ('capacite', 'effectif_actuel', 'places_disponibles'),
            'description': _('RG04 : Inscription impossible si effectif >= capacité.')
        }),
        (_('Encadrement'), {
            'fields': ('professeur_principal',)
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
            'school', 'academic_year', 'serie', 'professeur_principal', 'professeur_principal__user'
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'school':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        elif db_field.name == 'academic_year':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        elif db_field.name == 'serie':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        elif db_field.name == 'professeur_principal':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def effectif_actuel(self, obj):
        return obj.effectif_actuel
    effectif_actuel.short_description = _('Effectif')

    def places_disponibles(self, obj):
        return obj.places_disponibles
    places_disponibles.short_description = _('Places dispo')