from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# Choices pour les niveaux (MVP)
class Niveau(models.TextChoices):
    SIXIEME = '6eme', _('6ème')
    CINQUIEME = '5eme', _('5ème')
    QUATRIEME = '4eme', _('4ème')
    TROISIEME = '3eme', _('3ème')
    SECONDE = '2nde', _('2nde')
    PREMIERE = '1ere', _('1ère')
    TERMINALE = 'terminale', _('Terminale')


class Serie(models.Model):
    """
    Modèle Série (Serie).
    Utilisé pour les classes de 1ère et Terminale (A, B, C, D, G).
    Pas de série pour les niveaux collège (6ème à 3ème).
    """

    code = models.CharField(
        _('code'),
        max_length=10,
        unique=True,
        help_text=_('Code court: A, B, C, D, G')
    )
    nom = models.CharField(
        _('nom'),
        max_length=100,
        help_text=_('Ex: "Série A - Lettres", "Série C - Sciences"')
    )
    niveaux_concernes = models.JSONField(
        _('niveaux concernés'),
        default=list,
        help_text=_('Liste des niveaux: ["1ere", "terminale"]')
    )
    is_active = models.BooleanField(_('actif'), default=True)
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)

    class Meta:
        verbose_name = _('série')
        verbose_name_plural = _('séries')
        ordering = ['code']
        indexes = [
            models.Index(fields=['code'], name='serie_code_idx'),
            models.Index(fields=['is_active'], name='serie_active_idx'),
        ]

    def __str__(self):
        return f"{self.code} - {self.nom}"

    def clean(self):
        super().clean()
        self.code = self.code.upper().strip()
        self.nom = self.nom.strip()

        # Validation des niveaux concernés
        valid_niveaux = [n.value for n in Niveau]
        for niveau in self.niveaux_concernes:
            if niveau not in valid_niveaux:
                raise ValidationError({
                    'niveaux_concernes': _(f'Niveau invalide: {niveau}. Valeurs acceptées: {valid_niveaux}')
                })

        # Pour le MVP, les séries ne concernent que 1ère et Terminale
        allowed = {Niveau.PREMIERE, Niveau.TERMINALE}
        for niveau in self.niveaux_concernes:
            if niveau not in allowed:
                raise ValidationError({
                    'niveaux_concernes': _('Pour le MVP, les séries ne concernent que 1ère et Terminale.')
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # RG19 : Pas de suppression physique - on désactive
        self.is_active = False
        self.save(update_fields=['is_active', 'date_modification'])


class ClassRoom(models.Model):
    """
    Modèle Classe (ClassRoom).
    Appartient à un établissement (School) et une année scolaire (AcademicYear).
    Peut avoir une série (pour 1ère/Terminale) et un professeur principal.
    RG04 : Inscription impossible si effectif >= capacité.
    RG19 : Pas de suppression physique.
    """

    school = models.ForeignKey(
        'schools.School',
        on_delete=models.PROTECT,
        related_name='classrooms',
        verbose_name=_('établissement')
    )
    academic_year = models.ForeignKey(
        'schools.AcademicYear',
        on_delete=models.PROTECT,
        related_name='classrooms',
        verbose_name=_('année scolaire')
    )
    nom = models.CharField(
        _('nom'),
        max_length=50,
        help_text=_('Ex: "6ème A", "1ère D", "Terminale C"')
    )
    niveau = models.CharField(
        _('niveau'),
        max_length=20,
        choices=Niveau.choices,
        help_text=_('Niveau de la classe')
    )
    serie = models.ForeignKey(
        Serie,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classrooms',
        verbose_name=_('série'),
        help_text=_('Série pour 1ère/Terminale. Laisser vide pour le collège.')
    )
    capacite = models.PositiveIntegerField(
        _('capacité'),
        default=35,
        help_text=_('Nombre maximum d\'élèves (RG04)')
    )
    professeur_principal = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classes_principales',
        verbose_name=_('professeur principal')
    )
    is_active = models.BooleanField(
        _('actif'),
        default=True,
        help_text=_('Désactiver au lieu de supprimer (RG19)')
    )
    date_creation = models.DateTimeField(_('date de création'), auto_now_add=True)
    date_modification = models.DateTimeField(_('date de modification'), auto_now=True)

    class Meta:
        verbose_name = _('classe')
        verbose_name_plural = _('classes')
        ordering = ['school', 'academic_year', 'niveau', 'nom']
        constraints = [
            # UQ¹ : Nom unique par établissement par année scolaire
            models.UniqueConstraint(
                fields=['school', 'academic_year', 'nom'],
                name='unique_classroom_per_school_year'
            ),
        ]
        indexes = [
            models.Index(fields=['school', 'academic_year'], name='classroom_school_year_idx'),
            models.Index(fields=['school', 'niveau'], name='classroom_school_niveau_idx'),
            models.Index(fields=['academic_year', 'is_active'], name='classroom_year_active_idx'),
            models.Index(fields=['professeur_principal'], name='classroom_prof_principal_idx'),
        ]

    def __str__(self):
        return f"{self.nom} ({self.school.code} - {self.academic_year.nom})"

    def clean(self):
        super().clean()
        self.nom = self.nom.strip()

        # Validation : si niveau est 1ère ou Terminale, une série est requise
        if self.niveau in [Niveau.PREMIERE, Niveau.TERMINALE]:
            if not self.serie:
                raise ValidationError({
                    'serie': _('Une série est obligatoire pour les classes de 1ère et Terminale.')
                })
            # Vérifier que la série correspond au niveau
            if self.niveau not in self.serie.niveaux_concernes:
                raise ValidationError({
                    'serie': _(f'La série {self.serie.code} ne concerne pas le niveau {self.get_niveau_display()}.')
                })
        else:
            # Pour le collège, pas de série
            if self.serie:
                raise ValidationError({
                    'serie': _('Les classes de collège (6ème à 3ème) n\'ont pas de série.')
                })

        # Validation capacité positive (doit être > 0)
        if self.capacite is not None and self.capacite <= 0:
            raise ValidationError({
                'capacite': _('La capacité doit être un entier strictement positif.')
            })

        # Validation : professeur principal appartient à la même école
        if self.professeur_principal and self.professeur_principal.school != self.school:
            raise ValidationError({
                'professeur_principal': _('Le professeur principal doit appartenir au même établissement.')
            })

        # Validation : l'année scolaire appartient à la même école
        if self.academic_year.school != self.school:
            raise ValidationError({
                'academic_year': _('L\'année scolaire doit appartenir au même établissement.')
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # RG19 : Pas de suppression physique - on désactive
        self.is_active = False
        self.save(update_fields=['is_active', 'date_modification'])

    @property
    def effectif_actuel(self):
        """Effectif actuel des élèves inscrits (statut ACTIVE) pour RG04."""
        # La relation 'enrollments' sera disponible quand l'app enrollments sera créée
        if hasattr(self, 'enrollments'):
            return self.enrollments.filter(statut='ACTIVE').count()
        return 0

    @property
    def places_disponibles(self):
        """Places restantes dans la classe."""
        return max(0, self.capacite - self.effectif_actuel)

    @property
    def est_complete(self):
        """Vérifie si la classe a atteint sa capacité (RG04)."""
        return self.effectif_actuel >= self.capacite

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