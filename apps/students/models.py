from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Parent(models.Model):
    """
    Modèle Parent / Tuteur.
    Relation 1:1 avec User (role=PARENT).
    Relation 1:N vers Student (enfants).
    RG19 : Pas de suppression physique.
    """

    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='parent_profile',
        verbose_name=_('utilisateur')
    )
    profession = models.CharField(
        _('profession'),
        max_length=100,
        blank=True,
        default=''
    )
    revenu_mensuel = models.DecimalField(
        _('revenu mensuel'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        _('actif'),
        default=True,
        help_text=_('Désactiver au lieu de supprimer (RG19)')
    )
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)

    class Meta:
        verbose_name = _('parent / tuteur')
        verbose_name_plural = _('parents / tuteurs')
        ordering = ['user__last_name', 'user__first_name']
        indexes = [
            models.Index(fields=['is_active'], name='parent_active_idx'),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

    def clean(self):
        super().clean()
        # Vérifier que l'utilisateur a le rôle PARENT
        if self.user_id and self.user.role != 'PARENT':
            raise ValidationError({
                'user': _('L\'utilisateur associé doit avoir le rôle PARENT.')
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # RG19 : Pas de suppression physique - on désactive
        self.is_active = False
        self.save(update_fields=['is_active', 'date_modification'])


class Student(models.Model):
    """
    Modèle Élève (Student).
    Relation 1:1 avec User (role=STUDENT).
    Appartient à un établissement (School).
    Matricule unique par établissement : MAT-{year}-{seq:04d}.
    RG02 : Matricule unique dans l'établissement et généré automatiquement.
    RG19 : Pas de suppression physique.
    """

    class Sexe(models.TextChoices):
        MASCULIN = 'M', _('Masculin')
        FEMININ = 'F', _('Féminin')

    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='student_profile',
        verbose_name=_('utilisateur')
    )
    school = models.ForeignKey(
        'schools.School',
        on_delete=models.PROTECT,
        related_name='students',
        verbose_name=_('établissement')
    )
    matricule = models.CharField(
        _('matricule'),
        max_length=20,
        help_text=_('Format: MAT-{year}-{seq:04d} (ex: MAT-2026-0001)')
    )
    sexe = models.CharField(
        _('sexe'),
        max_length=1,
        choices=Sexe.choices
    )
    lieu_naissance = models.CharField(
        _('lieu de naissance'),
        max_length=100
    )
    nationalite = models.CharField(
        _('nationalité'),
        max_length=50,
        default='Béninoise'
    )
    parent = models.ForeignKey(
        Parent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enfants',
        verbose_name=_('parent / tuteur')
    )
    is_active = models.BooleanField(
        _('actif'),
        default=True,
        help_text=_('Désactiver au lieu de supprimer (RG19)')
    )
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)

    class Meta:
        verbose_name = _('élève')
        verbose_name_plural = _('élèves')
        ordering = ['school', 'matricule']
        constraints = [
            # RG02 : Matricule unique par établissement
            models.UniqueConstraint(
                fields=['school', 'matricule'],
                name='unique_matricule_per_school'
            ),
        ]
        indexes = [
            models.Index(fields=['school', 'is_active'], name='student_school_active_idx'),
            models.Index(fields=['matricule'], name='student_matricule_idx'),
            models.Index(fields=['parent'], name='student_parent_idx'),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.matricule})"

    def clean(self):
        super().clean()

        # Normalisation matricule en majuscules
        if self.matricule:
            self.matricule = self.matricule.upper().strip()

        # Vérifier que l'utilisateur a le rôle STUDENT
        if self.user_id and self.user.role != 'STUDENT':
            raise ValidationError({
                'user': _('L\'utilisateur associé doit avoir le rôle STUDENT.')
            })

        # Validation matricule format (après normalisation)
        import re
        if self.matricule and not re.match(r'^MAT-\d{4}-\d{4}$', self.matricule):
            raise ValidationError({
                'matricule': _('Le matricule doit respecter le format MAT-YYYY-NNNN (ex: MAT-2026-0001).')
            })

        # Validation : parent doit être actif
        if self.parent and not self.parent.is_active:
            raise ValidationError({
                'parent': _('Le parent associé doit être actif.')
            })

    def save(self, *args, **kwargs):
        # Génération automatique du matricule si non fourni
        if not self.matricule:
            self.matricule = self._generate_matricule()
        self.full_clean()
        super().save(*args, **kwargs)

    @transaction.atomic
    def _generate_matricule(self):
        """
        Génère un matricule MAT-{year}-{seq:04d} par établissement de façon thread-safe.
        Utilise select_for_update pour éviter les conditions de course.
        """
        # Année civile de début de l'année scolaire courante
        current_year = self.school.academic_year_current
        if current_year:
            year = current_year.date_debut.year
        else:
            year = timezone.now().year

        prefix = f'MAT-{year}-'

        # Verrouiller la table pour cette école/année pour éviter race condition
        last_student = Student.objects.select_for_update().filter(
            school=self.school,
            matricule__startswith=prefix
        ).order_by('-matricule').first()

        if last_student:
            try:
                last_seq = int(last_student.matricule.split('-')[-1])
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

    @property
    def inscriptions_actives(self):
        """Retourne les inscriptions actives de l'élève."""
        if hasattr(self, 'enrollments'):
            return self.enrollments.filter(statut='ACTIVE')
        return None

    @property
    def inscription_courante(self):
        """Retourne l'inscription de l'année scolaire courante."""
        if hasattr(self, 'enrollments'):
            current_year = self.school.academic_year_current
            if current_year:
                return self.enrollments.filter(
                    academic_year=current_year, statut='ACTIVE'
                ).first()
        return None