from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Teacher, TeachingAssignment


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    """Administration des enseignants."""

    list_display = [
        'user', 'matricule', 'school', 'specialite', 'statut',
        'date_embauche', 'is_active', 'date_creation'
    ]
    list_filter = ['school', 'statut', 'is_active', 'date_creation']
    search_fields = [
        'user__first_name', 'user__last_name', 'user__email',
        'matricule', 'specialite', 'diplome'
    ]
    ordering = ['school', 'user__last_name', 'user__first_name']
    readonly_fields = ['date_creation', 'date_modification', 'matricule']
    list_select_related = ['user', 'school']

    fieldsets = (
        (None, {
            'fields': ('user', 'school', 'matricule')
        }),
        (_('Informations professionnelles'), {
            'fields': ('specialite', 'diplome', 'date_embauche', 'statut')
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
        return super().get_queryset(request).select_related('user', 'school')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'school':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        elif db_field.name == 'user':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(role='TEACHER', is_active=True))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    """Administration des affectations d'enseignement."""

    list_display = [
        'teacher', 'subject', 'classroom', 'academic_year',
        'heures_prevues', 'is_active', 'date_creation'
    ]
    list_filter = [
        'academic_year', 'teacher__school', 'subject__niveau',
        'subject__serie', 'is_active', 'date_creation'
    ]
    search_fields = [
        'teacher__user__first_name', 'teacher__user__last_name',
        'subject__nom', 'subject__code', 'classroom__nom'
    ]
    ordering = ['academic_year', 'teacher', 'classroom', 'subject']
    readonly_fields = ['date_creation', 'date_modification']
    list_select_related = [
        'teacher', 'teacher__user', 'subject', 'classroom',
        'classroom__school', 'academic_year'
    ]

    fieldsets = (
        (None, {
            'fields': ('teacher', 'subject', 'classroom', 'academic_year')
        }),
        (_('Détails'), {
            'fields': ('heures_prevues',)
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
            'teacher', 'teacher__user', 'subject', 'classroom', 'academic_year'
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'teacher':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        elif db_field.name == 'subject':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        elif db_field.name == 'classroom':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        elif db_field.name == 'academic_year':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)