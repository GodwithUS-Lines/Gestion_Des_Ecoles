from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.schools.models import AcademicYear


class Enrollment(models.Model):
    """
    Modèle Inscription (Enrollment).
    Relie un élève, une classe et une année scolaire.
    RG03 : Une seule inscription par élève par année scolaire.
    RG04 : Inscription impossible si effectif classe >= capacité.
    RG05 : Numéro d'inscription automatique et unique par année scolaire (INS-{year}-{seq:04d}).
    RG19 : Pas de suppression physique.
    """

    class Statut(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        SUSPENDUE = 'SUSPENDUE', _('Suspendue')
        TERMINEE = 'TERMINEE', _('Terminée')
        ANNULEE = 'ANNULEE', _('Annulée')

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.PROTECT,
        related_name='enrollments',
        verbose_name=_('élève')
    )
    classroom = models.ForeignKey(
        'classes.ClassRoom',
        on_delete=models.PROTECT,
        related_name='enrollments',
        verbose_name=_('classe')
    )
    academic_year = models.ForeignKey(
        'schools.AcademicYear',
        on_delete=models.PROTECT,
        related_name='enrollments',
        verbose_name=_('année scolaire')
    )
    numero_inscription = models.CharField(
        _('numéro d\'inscription'),
        max_length=20,
        help_text=_('Format: INS-{year}-{seq:04d} (ex: INS-2026-0001)')
    )
    date_inscription = models.DateField(_('date d\'inscription'), auto_now_add=True)
    statut = models.CharField(
        _('statut'),
        max_length=20,
        choices=Statut.choices,
        default=Statut.ACTIVE
    )
    is_reinscription = models.BooleanField(
        _('réinscription'),
        default=False,
        help_text=_('True si l\'élève était déjà inscrit l\'année précédente')
    )
    is_active = models.BooleanField(
        _('actif'),
        default=True,
        help_text=_('Désactiver au lieu de supprimer (RG19)')
    )
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)

    class Meta:
        verbose_name = _('inscription')
        verbose_name_plural = _('inscriptions')
        ordering = ['academic_year', 'student']
        constraints = [
            # RG03 : Une seule inscription par élève par année scolaire
            models.UniqueConstraint(
                fields=['student', 'academic_year'],
                name='unique_enrollment_per_student_per_year'
            ),
            # RG05 (UQ²) : Numéro d'inscription unique par année scolaire
            models.UniqueConstraint(
                fields=['academic_year', 'numero_inscription'],
                name='unique_inscription_number_per_year'
            ),
        ]
        indexes = [
            models.Index(fields=['student', 'academic_year'], name='enroll_student_year_idx'),
            models.Index(fields=['classroom', 'academic_year'], name='enroll_classroom_year_idx'),
            models.Index(fields=['academic_year', 'statut'], name='enroll_year_statut_idx'),
            models.Index(fields=['is_active'], name='enroll_active_idx'),
        ]

    def __str__(self):
        return f"{self.student} - {self.classroom} ({self.academic_year}) - {self.get_statut_display()}"

    def clean(self):
        super().clean()

        # Normalisation numéro inscription
        if self.numero_inscription:
            self.numero_inscription = self.numero_inscription.upper().strip()

        # Validation format numéro inscription
        import re
        if self.numero_inscription and not re.match(r'^INS-\d{4}-\d{4}$', self.numero_inscription):
            raise ValidationError({
                'numero_inscription': _('Le numéro d\'inscription doit respecter le format INS-YYYY-NNNN (ex: INS-2026-0001).')
            })

        # Validation cohérence établissement
        errors = {}
        if self.student_id is None:
            return errors
        school = self.student.school

        if self.classroom_id is not None:
            if self.classroom.school != school:
                errors['classroom'] = _('La classe doit appartenir au même établissement que l\'élève.')

            if self.academic_year_id is not None:
                if self.academic_year.school != school:
                    errors['academic_year'] = _('L\'année scolaire doit appartenir au même établissement que l\'élève.')

                # Validation niveau élève compatible avec classe (si élève a un niveau via inscription précédente)
                # Pour l'instant on vérifie seulement la cohérence classe/année
                if self.classroom.academic_year != self.academic_year:
                    errors['classroom'] = _('La classe doit appartenir à l\'année scolaire sélectionnée.')

        # RG04 : Vérifier capacité de la classe (seulement pour inscriptions actives)
        if self.statut == self.Statut.ACTIVE and self.classroom_id is not None:
            # Si c'est une nouvelle inscription ou changement vers ACTIVE
            if not self.pk or Enrollment.objects.filter(pk=self.pk, statut=self.Statut.ACTIVE).exists() is False:
                if self.classroom.est_complete:
                    errors['classroom'] = _(
                        f'La classe {self.classroom.nom} a atteint sa capacité maximale '
                        f'({self.classroom.capacite} élèves).'
                    )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Génération automatique du numéro d'inscription si non fourni
        if not self.numero_inscription:
            self.numero_inscription = self._generate_numero_inscription()
        
        # Détection réinscription
        if not self.pk and not self.is_reinscription:
            self.is_reinscription = self._check_reinscription()
        
        self.full_clean()
        super().save(*args, **kwargs)

    @transaction.atomic
    def _generate_numero_inscription(self):
        """
        Génère un numéro d'inscription INS-{year}-{seq:04d} par année scolaire de façon thread-safe.
        UQ² : unique par année scolaire.
        """
        # Année civile de début de l'année scolaire
        year = self.academic_year.date_debut.year
        prefix = f'INS-{year}-'

        # Verrouiller pour cette année scolaire
        last_enrollment = Enrollment.objects.select_for_update().filter(
            academic_year=self.academic_year,
            numero_inscription__startswith=prefix
        ).order_by('-numero_inscription').first()

        if last_enrollment:
            try:
                last_seq = int(last_enrollment.numero_inscription.split('-')[-1])
                seq = last_seq + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f'{prefix}{seq:04d}'

    def _check_reinscription(self):
        """Vérifie si l'élève était inscrit l'année précédente."""
        previous_year = AcademicYear.objects.filter(
            school=self.student.school,
            date_fin__lt=self.academic_year.date_debut
        ).order_by('-date_fin').first()
        
        if previous_year:
            return Enrollment.objects.filter(
                student=self.student,
                academic_year=previous_year,
                statut__in=[self.Statut.ACTIVE, self.Statut.TERMINEE]
            ).exists()
        return False

    def delete(self, *args, **kwargs):
        # RG19 : Pas de suppression physique - on désactive
        self.is_active = False
        self.save(update_fields=['is_active', 'date_modification'])

    def annuler(self):
        """Annule l'inscription (statut ANNULEE) en conservant l'historique."""
        self.statut = self.Statut.ANNULEE
        self.is_active = False
        self.save(update_fields=['statut', 'is_active', 'date_modification'])

    def terminer(self):
        """Termine l'inscription (statut TERMINEE) - fin d'année normale."""
        self.statut = self.Statut.TERMINEE
        self.save(update_fields=['statut', 'date_modification'])

    def suspendre(self):
        """Suspend l'inscription."""
        self.statut = self.Statut.SUSPENDUE
        self.save(update_fields=['statut', 'date_modification'])

    def reactiver(self):
        """Réactive une inscription suspendue."""
        if self.statut == self.Statut.SUSPENDUE:
            self.statut = self.Statut.ACTIVE
            self.save(update_fields=['statut', 'date_modification'])

    @property
    def est_active(self):
        """Vérifie si l'inscription est active."""
        return self.statut == self.Statut.ACTIVE and self.is_active