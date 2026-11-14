from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class School(models.Model):
    """
    Modèle Établissement (School).
    Représente un établissement scolaire secondaire.
    Relation 1:N vers AcademicYear, ClassRoom, Subject, Student, Teacher.
    """

    nom = models.CharField(_('nom'), max_length=200)
    code = models.CharField(
        _('code établissement'),
        max_length=20,
        unique=True,
        help_text=_('Code court unique (ex: LYC01, COL02) utilisé pour les matricules')
    )
    logo = models.ImageField(
        _('logo'),
        upload_to='schools/logos/',
        null=True,
        blank=True
    )
    adresse = models.TextField(_('adresse'))
    telephone = models.CharField(_('téléphone'), max_length=20)
    email = models.EmailField(_('email'))
    directeur_nom = models.CharField(_('nom du directeur'), max_length=150)
    is_active = models.BooleanField(
        _('actif'),
        default=True,
        help_text=_('Désactiver au lieu de supprimer (RG19)')
    )
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)

    class Meta:
        verbose_name = _('établissement')
        verbose_name_plural = _('établissements')
        ordering = ['nom']
        indexes = [
            models.Index(fields=['code'], name='school_code_idx'),
            models.Index(fields=['is_active'], name='school_active_idx'),
        ]

    def __str__(self):
        return self.nom

    def clean(self):
        super().clean()
        self.code = self.code.upper().strip()
        self.nom = self.nom.strip()
        self.email = self.email.lower().strip()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # RG19 : Pas de suppression physique - on désactive
        self.is_active = False
        self.save(update_fields=['is_active', 'date_modification'])

    @property
    def academic_year_current(self):
        """Retourne l'année scolaire active (is_current=True) pour cet établissement (RG01)."""
        return self.academic_years.filter(is_current=True, is_active=True).first()

    @property
    def students_count(self):
        # Relation 'students' sera disponible quand l'app students sera créée
        if hasattr(self, 'students'):
            return self.students.filter(is_active=True).count()
        return 0

    @property
    def teachers_count(self):
        if hasattr(self, 'teachers'):
            return self.teachers.filter(is_active=True).count()
        return 0

    @property
    def classrooms_count(self):
        if hasattr(self, 'classrooms'):
            return self.classrooms.filter(is_active=True).count()
        return 0


class AcademicYear(models.Model):
    """
    Modèle Année scolaire (AcademicYear).
    Appartient à un établissement (School).
    RG01 : Une seule année scolaire active (is_current) par établissement.
    """

    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name='academic_years',
        verbose_name=_('établissement')
    )
    nom = models.CharField(
        _('nom'),
        max_length=50,
        help_text=_('Format: "2026-2027"')
    )
    date_debut = models.DateField(_('date de début'))
    date_fin = models.DateField(_('date de fin'))
    is_current = models.BooleanField(
        _('année courante'),
        default=False,
        help_text=_('Une seule année courante par établissement (RG01)')
    )
    is_active = models.BooleanField(_('actif'), default=True)
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)

    class Meta:
        verbose_name = _('année scolaire')
        verbose_name_plural = _('années scolaires')
        ordering = ['-date_debut']
        constraints = [
            # RG01 : Une seule année courante par établissement
            models.UniqueConstraint(
                fields=['school', 'is_current'],
                condition=Q(is_current=True),
                name='unique_current_year_per_school'
            ),
            # Nom unique par établissement
            models.UniqueConstraint(
                fields=['school', 'nom'],
                name='unique_year_name_per_school'
            ),
        ]
        indexes = [
            models.Index(fields=['school', 'is_current'], name='acadyear_school_current_idx'),
            models.Index(fields=['school', 'is_active'], name='acadyear_school_active_idx'),
            models.Index(fields=['date_debut', 'date_fin'], name='acadyear_dates_idx'),
        ]

    def __str__(self):
        return f"{self.nom} ({self.school.nom})"

    def clean(self):
        super().clean()
        self.nom = self.nom.strip()

        # Validation dates
        if self.date_debut and self.date_fin:
            if self.date_debut >= self.date_fin:
                raise ValidationError({
                    'date_fin': _('La date de fin doit être postérieure à la date de début.')
                })

        # RG01 : Si on définit is_current=True, vérifier qu'aucune autre année n'est current pour cette école
        if self.is_current:
            qs = AcademicYear.objects.filter(school=self.school, is_current=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({
                    'is_current': _('Une autre année scolaire est déjà définie comme courante pour cet établissement (RG01).')
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # RG19 : Pas de suppression physique - on désactive
        self.is_active = False
        self.save(update_fields=['is_active', 'date_modification'])

    @property
    def is_ongoing(self):
        """Vérifie si l'année scolaire est en cours (basé sur dates)."""
        from django.utils import timezone
        today = timezone.now().date()
        return self.date_debut <= today <= self.date_fin