from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Teacher(models.Model):
    """
    Modèle Enseignant (Teacher).
    Relation 1:1 avec User, FK vers School.
    Matricule unique par établissement, généré automatiquement : ENS-{year}-{seq:04d}.
    RG19 : Pas de suppression physique.
    """

    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='teacher_profile',
        verbose_name=_('utilisateur')
    )
    school = models.ForeignKey(
        'schools.School',
        on_delete=models.PROTECT,
        related_name='teachers',
        verbose_name=_('établissement')
    )
    matricule = models.CharField(
        _('matricule'),
        max_length=20,
        help_text=_('Format: ENS-{year}-{seq:04d} (ex: ENS-2026-0001)')
    )
    specialite = models.CharField(_('spécialité'), max_length=100, blank=True)
    diplome = models.CharField(_('diplôme'), max_length=200, blank=True)
    date_embauche = models.DateField(_('date d\'embauche'), null=True, blank=True)
    statut = models.CharField(
        _('statut'),
        max_length=20,
        choices=[
            ('TITULAIRE', _('Titulaire')),
            ('VACATAIRE', _('Vacataire')),
            ('STAGIAIRE', _('Stagiaire')),
        ],
        default='TITULAIRE'
    )
    is_active = models.BooleanField(
        _('actif'),
        default=True,
        help_text=_('Désactiver au lieu de supprimer (RG19)')
    )
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)

    class Meta:
        verbose_name = _('enseignant')
        verbose_name_plural = _('enseignants')
        ordering = ['user__last_name', 'user__first_name']
        constraints = [
            # UQ¹ : Matricule unique par établissement
            models.UniqueConstraint(
                fields=['school', 'matricule'],
                name='unique_teacher_matricule_per_school'
            ),
        ]
        indexes = [
            models.Index(fields=['school', 'is_active'], name='teacher_school_active_idx'),
            models.Index(fields=['matricule'], name='teacher_matricule_idx'),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.matricule})"

    def clean(self):
        super().clean()
        self.matricule = self.matricule.upper().strip()

        # Validation format matricule
        import re
        if self.matricule and not re.match(r'^ENS-\d{4}-\d{4}$', self.matricule):
            raise ValidationError({
                'matricule': _('Le matricule doit respecter le format ENS-YYYY-NNNN (ex: ENS-2026-0001).')
            })

    def save(self, *args, **kwargs):
        # Génération automatique du matricule si non fourni
        if not self.matricule:
            self.matricule = self._generate_matricule()
        self.full_clean()
        super().save(*args, **kwargs)

    def _generate_matricule(self):
        """Génère un matricule ENS-{year}-{seq:04d} par établissement."""
        # Année civile de début de l'année scolaire courante
        current_year = self.school.academic_year_current
        if current_year:
            year = current_year.date_debut.year
        else:
            year = timezone.now().year

        # Trouver la dernière séquence pour cette école et cette année
        prefix = f'ENS-{year}-'
        last_teacher = Teacher.objects.filter(
            school=self.school,
            matricule__startswith=prefix
        ).order_by('-matricule').first()

        if last_teacher:
            try:
                last_seq = int(last_teacher.matricule.split('-')[-1])
                seq = last_seq + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f'{prefix}{seq:04d}'

    def delete(self, *args, **kwargs):
        # RG19 : Pas de suppression physique - on désactive
        self.is_active = False
        self.save(update_fields=['is_active', 'date_modification'])


class TeachingAssignment(models.Model):
    """
    Modèle Affectation d'enseignement (TeachingAssignment).
    Relie un enseignant, une matière et une classe pour une année scolaire donnée.
    RG06 : Un enseignant ne saisit notes/absences que pour ses affectations.
    RG19 : Pas de suppression physique.
    """

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name='assignments',
        verbose_name=_('enseignant')
    )
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.PROTECT,
        related_name='assignments',
        verbose_name=_('matière')
    )
    classroom = models.ForeignKey(
        'classes.ClassRoom',
        on_delete=models.PROTECT,
        related_name='assignments',
        verbose_name=_('classe')
    )
    academic_year = models.ForeignKey(
        'schools.AcademicYear',
        on_delete=models.PROTECT,
        related_name='assignments',
        verbose_name=_('année scolaire')
    )
    heures_prevues = models.PositiveIntegerField(
        _('heures prévues'),
        default=0,
        help_text=_('Nombre d\'heures d\'enseignement prévues par semaine')
    )
    is_active = models.BooleanField(
        _('actif'),
        default=True,
        help_text=_('Désactiver au lieu de supprimer (RG19)')
    )
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)

    class Meta:
        verbose_name = _('affectation d\'enseignement')
        verbose_name_plural = _('affectations d\'enseignement')
        ordering = ['teacher', 'academic_year', 'classroom', 'subject']
        constraints = [
            # Unicité : un enseignant ne peut avoir qu'une affectation pour une matière/classe/année
            models.UniqueConstraint(
                fields=['teacher', 'subject', 'classroom', 'academic_year'],
                name='unique_teaching_assignment'
            ),
        ]
        indexes = [
            models.Index(fields=['teacher', 'academic_year'], name='ta_teacher_year_idx'),
            models.Index(fields=['subject', 'academic_year'], name='ta_subject_year_idx'),
            models.Index(fields=['classroom', 'academic_year'], name='ta_classroom_year_idx'),
            models.Index(fields=['is_active'], name='ta_active_idx'),
        ]

    def __str__(self):
        return f"{self.teacher} - {self.subject} - {self.classroom} ({self.academic_year})"

    def clean(self):
        super().clean()

        # Validation cohérence établissement
        school = self.teacher.school
        errors = {}

        if self.subject.school != school:
            errors['subject'] = _('La matière doit appartenir au même établissement que l\'enseignant.')

        if self.classroom.school != school:
            errors['classroom'] = _('La classe doit appartenir au même établissement que l\'enseignant.')

        if self.academic_year.school != school:
            errors['academic_year'] = _('L\'année scolaire doit appartenir au même établissement que l\'enseignant.')

        # Validation cohérence niveau matière vs classe
        if self.subject.niveau != self.classroom.niveau:
            errors['subject'] = _(
                f'La matière est pour le niveau {self.subject.get_niveau_display()} '
                f'alors que la classe est de niveau {self.classroom.get_niveau_display()}.'
            )

        # Validation cohérence série matière vs classe
        if self.subject.serie != self.classroom.serie:
            errors['subject'] = _('La série de la matière doit correspondre à la série de la classe.')

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # RG19 : Pas de suppression physique - on désactive
        self.is_active = False
        self.save(update_fields=['is_active', 'date_modification'])

    @property
    def enseignant_peut_saisir_notes(self):
        """Vérifie si l'enseignant peut saisir notes pour cette affectation (RG06)."""
        return self.is_active and self.teacher.is_active and self.subject.is_active and self.classroom.is_active

    @property
    def enseignant_peut_saisir_absences(self):
        """Vérifie si l'enseignant peut saisir absences pour cette affectation (RG06)."""
        return self.enseignant_peut_saisir_notes