from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Administration des inscriptions."""

    list_display = [
        'student', 'classroom', 'academic_year', 'numero_inscription',
        'date_inscription', 'statut', 'is_reinscription', 'is_active'
    ]
    list_filter = [
        'academic_year', 'classroom__school', 'classroom__niveau',
        'classroom__serie', 'statut', 'is_reinscription', 'is_active'
    ]
    search_fields = [
        'student__user__first_name', 'student__user__last_name',
        'student__matricule', 'numero_inscription'
    ]
    ordering = ['-academic_year', 'classroom', 'student']
    readonly_fields = ['date_inscription', 'date_creation', 'date_modification', 'numero_inscription']
    list_select_related = [
        'student', 'student__user', 'student__school',
        'classroom', 'classroom__school', 'classroom__serie',
        'academic_year'
    ]

    fieldsets = (
        (None, {
            'fields': ('student', 'classroom', 'academic_year', 'numero_inscription')
        }),
        (_('Statut'), {
            'fields': ('statut', 'is_reinscription', 'is_active')
        }),
        (_('Dates'), {
            'fields': ('date_inscription', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student', 'student__user', 'student__school',
            'classroom', 'classroom__school', 'classroom__serie',
            'academic_year'
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'student':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        elif db_field.name == 'classroom':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        elif db_field.name == 'academic_year':
            kwargs['queryset'] = kwargs.get('queryset', db_field.related_model.objects.filter(is_active=True))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    actions = ['annuler_inscriptions', 'terminer_inscriptions', 'suspendre_inscriptions']

    def annuler_inscriptions(self, request, queryset):
        """Action pour annuler les inscriptions sélectionnées."""
        count = 0
        for enrollment in queryset:
            if enrollment.statut != Enrollment.Statut.ANNULEE:
                enrollment.annuler()
                count += 1
        self.message_user(request, f'{count} inscription(s) annulée(s).')
    annuler_inscriptions.short_description = _('Annuler les inscriptions sélectionnées')

    def terminer_inscriptions(self, request, queryset):
        """Action pour terminer les inscriptions sélectionnées."""
        count = 0
        for enrollment in queryset:
            if enrollment.statut == Enrollment.Statut.ACTIVE:
                enrollment.terminer()
                count += 1
        self.message_user(request, f'{count} inscription(s) terminée(s).')
    terminer_inscriptions.short_description = _('Terminer les inscriptions sélectionnées')

    def suspendre_inscriptions(self, request, queryset):
        """Action pour suspendre les inscriptions sélectionnées."""
        count = 0
        for enrollment in queryset:
            if enrollment.statut == Enrollment.Statut.ACTIVE:
                enrollment.suspendre()
                count += 1
        self.message_user(request, f'{count} inscription(s) suspendue(s).')
    suspendre_inscriptions.short_description = _('Suspendre les inscriptions sélectionnées')