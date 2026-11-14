from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# Réutiliser les choix de niveaux depuis classes
class Niveau(models.TextChoices):
    SIXIEME = '6eme', _('6ème')
    CINQUIEME = '5eme', _('5ème')
    QUATRIEME = '4eme', _('4ème')
    TROISIEME = '3eme', _('3ème')
    SECONDE = '2nde', _('2nde')
    PREMIERE = '1ere', _('1ère')
    TERMINALE = 'terminale', _('Terminale')


class Subject(models.Model):
    """
    Modèle Matière (Subject).
    Appartient à un établissement (School).
    A un coefficient, un niveau, optionnellement une série (pour 1ère/Terminale)
    et un enseignant responsable.
    Relation N:M avec Teacher et ClassRoom via TeachingAssignment (dans app teachers).
    """

    school = models.ForeignKey(
        'schools.School',
        on_delete=models.PROTECT,
        related_name='subjects',
        verbose_name=_('établissement')
    )
    nom = models.CharField(_('nom'), max_length=100)
    code = models.CharField(
        _('code'),
        max_length=20,
        help_text=_('Code court unique par établissement (ex: MATH, FR, PC, SVT)')
    )
    coefficient = models.DecimalField(
        _('coefficient'),
        max_digits=4,
        decimal_places=2,
        default=1.0,
        help_text=_('Coefficient de la matière pour les moyennes (ex: 1.00, 2.00, 3.00)')
    )
    niveau = models.CharField(
        _('niveau'),
        max_length=20,
        choices=Niveau.choices,
        help_text=_('Niveau où la matière est enseignée')
    )
    serie = models.ForeignKey(
        'classes.Serie',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subjects',
        verbose_name=_('série'),
        help_text=_('Série pour 1ère/Terminale. Laisser vide pour collège et 2nde.')
    )
    enseignant_responsable = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matieres_responsables',
        verbose_name=_('enseignant responsable')
    )
    is_active = models.BooleanField(
        _('actif'),
        default=True,
        help_text=_('Désactiver au lieu de supprimer (RG19)')
    )
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)

    class Meta:
        verbose_name = _('matière')
        verbose_name_plural = _('matières')
        ordering = ['school', 'niveau', 'nom']
        constraints = [
            # UQ¹ : Code unique par établissement
            models.UniqueConstraint(
                fields=['school', 'code'],
                name='unique_subject_code_per_school'
            ),
        ]
        indexes = [
            models.Index(fields=['school', 'niveau'], name='subject_school_niveau_idx'),
            models.Index(fields=['school', 'is_active'], name='subject_school_active_idx'),
            models.Index(fields=['enseignant_responsable'], name='subject_ens_resp_idx'),
        ]

    def __str__(self):
        return f"{self.nom} ({self.code}) - {self.get_niveau_display()}"

    def clean(self):
        super().clean()
        self.code = self.code.upper().strip()
        self.nom = self.nom.strip()

        # Validation coefficient > 0
        if self.coefficient is not None and self.coefficient <= 0:
            raise ValidationError({
                'coefficient': _('Le coefficient doit être strictement positif.')
            })

        # Validation : si niveau est 1ère ou Terminale, une série est optionnelle mais si définie doit correspondre
        if self.niveau in [Niveau.PREMIERE, Niveau.TERMINALE]:
            if self.serie:
                if self.niveau not in self.serie.niveaux_concernes:
                    raise ValidationError({
                        'serie': _(f'La série {self.serie.code} ne concerne pas le niveau {self.get_niveau_display()}.')
                    })
        else:
            # Pour le collège (6ème-3ème) et 2nde, pas de série
            if self.serie:
                raise ValidationError({
                    'serie': _('Les matières de collège (6ème à 3ème) et 2nde n\'ont pas de série.')
                })

        # Validation : enseignant responsable appartient à la même école
        if self.enseignant_responsable and self.enseignant_responsable.school != self.school:
            raise ValidationError({
                'enseignant_responsable': _('L\'enseignant responsable doit appartenir au même établissement.')
            })

        # Validation : la série (si définie) appartient à la même école (via AcademicYear/ClassRoom)
        # Note: Serie n'a pas de FK direct vers School, mais on peut vérifier via les ClassRoom
        # Pour l'instant on laisse car Serie est globale ou par école selon contexte futur

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # RG19 : Pas de suppression physique - on désactive
        self.is_active = False
        self.save(update_fields=['is_active', 'date_modification'])

    @property
    def niveau_est_college(self):
        """Vérifie si le niveau est un niveau collège."""
        return self.niveau in [
            Niveau.SIXIEME, Niveau.CINQUIEME,
            Niveau.QUATRIEME, Niveau.TROISIEME
        ]

    @property
    def niveau_est_lycee(self):
        """Vérifie si le niveau est un niveau lycée."""
        return self.niveau in [
            Niveau.SECONDE, Niveau.PREMIERE, Niveau.TERMINALE
        ]

    @property
    def enseignements_actuels(self):
        """Retourne les affectations actives (TeachingAssignment) pour cette matière."""
        # Relation disponible quand TeachingAssignment existera
        if hasattr(self, 'assignments'):
            return self.assignments.filter(is_active=True)
        return None