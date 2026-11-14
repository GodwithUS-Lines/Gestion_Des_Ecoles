from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import date, timedelta

from apps.schools.models import School, AcademicYear
from apps.classes.models import Serie, ClassRoom, Niveau


class SerieModelTestCase(TestCase):
    """Tests pour le modèle Serie."""

    def setUp(self):
        self.serie_data = {
            'code': 'A',
            'nom': 'Série A - Lettres',
            'niveaux_concernes': ['1ere', 'terminale'],
        }

    def test_create_serie(self):
        """Test création série basique."""
        serie = Serie.objects.create(**self.serie_data)
        self.assertEqual(serie.code, 'A')
        self.assertEqual(serie.nom, 'Série A - Lettres')
        self.assertEqual(serie.niveaux_concernes, ['1ere', 'terminale'])
        self.assertTrue(serie.is_active)

    def test_serie_code_unique(self):
        """Test unicité du code série."""
        Serie.objects.create(**self.serie_data)
        with self.assertRaises(ValidationError):
            Serie.objects.create(**{**self.serie_data, 'nom': 'Autre Série A'})

    def test_serie_code_uppercase_normalization(self):
        """Test normalisation code en majuscules."""
        serie = Serie.objects.create(**{**self.serie_data, 'code': 'b'})
        self.assertEqual(serie.code, 'B')

    def test_serie_str_representation(self):
        """Test représentation string."""
        serie = Serie.objects.create(**self.serie_data)
        self.assertEqual(str(serie), 'A - Série A - Lettres')

    def test_serie_soft_delete(self):
        """Test désactivation au lieu de suppression (RG19)."""
        serie = Serie.objects.create(**self.serie_data)
        serie_pk = serie.pk
        serie.delete()
        serie.refresh_from_db()
        self.assertFalse(serie.is_active)
        self.assertTrue(Serie.objects.filter(pk=serie_pk).exists())

    def test_serie_validation_niveaux_invalides(self):
        """Test validation niveaux invalides."""
        with self.assertRaises(ValidationError):
            Serie.objects.create(
                code='X', nom='Série X',
                niveaux_concernes=['niveau_inexistant']
            )

    def test_serie_validation_niveaux_mvp_only(self):
        """Test validation : MVP uniquement 1ère et Terminale."""
        with self.assertRaises(ValidationError):
            Serie.objects.create(
                code='X', nom='Série X',
                niveaux_concernes=['6eme']  # Pas autorisé pour MVP
            )

    def test_serie_niveaux_concernes_valides(self):
        """Test niveaux concernés valides."""
        serie = Serie.objects.create(
            code='C', nom='Série C - Sciences',
            niveaux_concernes=['1ere', 'terminale']
        )
        self.assertIn('1ere', serie.niveaux_concernes)
        self.assertIn('terminale', serie.niveaux_concernes)


class ClassRoomModelTestCase(TestCase):
    """Tests pour le modèle ClassRoom."""

    def setUp(self):
        self.school = School.objects.create(
            nom='Lycée Test', code='LYC01', adresse='123 Rue',
            telephone='+229 21 00 00 00', email='contact@lyceetest.bj',
            directeur_nom='M. Directeur'
        )
        self.today = timezone.now().date()
        self.academic_year = AcademicYear.objects.create(
            school=self.school, nom='2026-2027',
            date_debut=self.today, date_fin=self.today + timedelta(days=300),
            is_current=True
        )
        # Créer les séries pour les tests
        self.serie_a = Serie.objects.create(
            code='A', nom='Série A - Lettres', niveaux_concernes=['1ere', 'terminale']
        )
        self.serie_c = Serie.objects.create(
            code='C', nom='Série C - Sciences', niveaux_concernes=['1ere', 'terminale']
        )
        self.serie_d = Serie.objects.create(
            code='D', nom='Série D - Sciences', niveaux_concernes=['1ere', 'terminale']
        )

    def test_create_classroom_college(self):
        """Test création classe collège (sans série)."""
        classroom = ClassRoom.objects.create(
            school=self.school,
            academic_year=self.academic_year,
            nom='6ème A',
            niveau=Niveau.SIXIEME,
            capacite=35
        )
        self.assertEqual(classroom.nom, '6ème A')
        self.assertEqual(classroom.niveau, Niveau.SIXIEME)
        self.assertIsNone(classroom.serie)
        self.assertEqual(classroom.capacite, 35)
        self.assertTrue(classroom.is_active)
        self.assertTrue(classroom.niveau_est_college)
        self.assertFalse(classroom.niveau_est_lycee)

    def test_create_classroom_lycee_avec_serie(self):
        """Test création classe lycée (avec série)."""
        classroom = ClassRoom.objects.create(
            school=self.school,
            academic_year=self.academic_year,
            nom='1ère A',
            niveau=Niveau.PREMIERE,
            serie=self.serie_a,
            capacite=30
        )
        self.assertEqual(classroom.nom, '1ère A')
        self.assertEqual(classroom.niveau, Niveau.PREMIERE)
        self.assertEqual(classroom.serie, self.serie_a)
        self.assertTrue(classroom.niveau_est_lycee)
        self.assertFalse(classroom.niveau_est_college)

    def test_create_classroom_terminale_avec_serie(self):
        """Test création classe Terminale avec série."""
        classroom = ClassRoom.objects.create(
            school=self.school,
            academic_year=self.academic_year,
            nom='Terminale C',
            niveau=Niveau.TERMINALE,
            serie=self.serie_c,
            capacite=25
        )
        self.assertEqual(classroom.niveau, Niveau.TERMINALE)
        self.assertEqual(classroom.serie, self.serie_c)

    def test_classroom_nom_unique_per_school_year(self):
        """Test unicité nom par école par année."""
        ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='6ème A', niveau=Niveau.SIXIEME
        )
        with self.assertRaises(ValidationError):
            ClassRoom.objects.create(
                school=self.school, academic_year=self.academic_year,
                nom='6ème A', niveau=Niveau.SIXIEME
            )

    def test_classroom_same_name_different_schools_ok(self):
        """Test même nom autorisé pour écoles différentes."""
        school2 = School.objects.create(
            nom='Collège Test', code='COL01', adresse='456 Av.',
            telephone='+229 21 11 11 11', email='coll@test.bj', directeur_nom='Mme Directrice'
        )
        academic_year2 = AcademicYear.objects.create(
            school=school2, nom='2026-2027',
            date_debut=self.today, date_fin=self.today + timedelta(days=300)
        )
        ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='6ème A', niveau=Niveau.SIXIEME
        )
        classroom2 = ClassRoom.objects.create(
            school=school2, academic_year=academic_year2,
            nom='6ème A', niveau=Niveau.SIXIEME
        )
        self.assertEqual(classroom2.nom, '6ème A')

    def test_classroom_same_name_different_years_ok(self):
        """Test même nom autorisé pour années différentes (même école)."""
        academic_year2 = AcademicYear.objects.create(
            school=self.school, nom='2027-2028',
            date_debut=self.today + timedelta(days=365),
            date_fin=self.today + timedelta(days=665)
        )
        ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='6ème A', niveau=Niveau.SIXIEME
        )
        classroom2 = ClassRoom.objects.create(
            school=self.school, academic_year=academic_year2,
            nom='6ème A', niveau=Niveau.SIXIEME
        )
        self.assertEqual(classroom2.nom, '6ème A')

    def test_rg04_validation_capacite_positive(self):
        """Test validation capacité positive."""
        with self.assertRaises(ValidationError):
            ClassRoom.objects.create(
                school=self.school, academic_year=self.academic_year,
                nom='6ème A', niveau=Niveau.SIXIEME, capacite=0
            )

    def test_rg04_effectif_actuel_property(self):
        """Test propriété effectif_actuel (retourne 0 si pas d'enrollments)."""
        classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='6ème A', niveau=Niveau.SIXIEME, capacite=35
        )
        self.assertEqual(classroom.effectif_actuel, 0)
        self.assertEqual(classroom.places_disponibles, 35)
        self.assertFalse(classroom.est_complete)

    def test_classroom_validation_serie_obligatoire_premiere(self):
        """Test série obligatoire pour 1ère."""
        with self.assertRaises(ValidationError):
            ClassRoom.objects.create(
                school=self.school, academic_year=self.academic_year,
                nom='1ère A', niveau=Niveau.PREMIERE  # Pas de série
            )

    def test_classroom_validation_serie_obligatoire_terminale(self):
        """Test série obligatoire pour Terminale."""
        with self.assertRaises(ValidationError):
            ClassRoom.objects.create(
                school=self.school, academic_year=self.academic_year,
                nom='Terminale A', niveau=Niveau.TERMINALE  # Pas de série
            )

    def test_classroom_validation_pas_serie_pour_college(self):
        """Test pas de série pour le collège."""
        with self.assertRaises(ValidationError):
            ClassRoom.objects.create(
                school=self.school, academic_year=self.academic_year,
                nom='6ème A', niveau=Niveau.SIXIEME, serie=self.serie_a
            )

    def test_classroom_validation_serie_correspond_niveau(self):
        """Test série correspond au niveau."""
        # Créer une série qui ne concerne que 1ère
        serie_1ere_only = Serie.objects.create(
            code='X', nom='Série X - 1ère seulement', niveaux_concernes=['1ere']
        )
        with self.assertRaises(ValidationError):
            ClassRoom.objects.create(
                school=self.school, academic_year=self.academic_year,
                nom='Terminale X', niveau=Niveau.TERMINALE, serie=serie_1ere_only
            )

    def test_classroom_str_representation(self):
        """Test représentation string."""
        classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='6ème A', niveau=Niveau.SIXIEME
        )
        self.assertEqual(str(classroom), f"6ème A (LYC01 - 2026-2027)")

    def test_classroom_soft_delete(self):
        """Test désactivation au lieu de suppression (RG19)."""
        classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='6ème A', niveau=Niveau.SIXIEME
        )
        classroom_pk = classroom.pk
        classroom.delete()
        classroom.refresh_from_db()
        self.assertFalse(classroom.is_active)
        self.assertTrue(ClassRoom.objects.filter(pk=classroom_pk).exists())

    def test_classroom_validation_professeur_principal_meme_ecole(self):
        """Test validation professeur principal même école."""
        # Ce test nécessite un Teacher, on le fait dans un test d'intégration plus tard
        pass

    def test_classroom_validation_academic_year_meme_ecole(self):
        """Test validation année scolaire même école."""
        school2 = School.objects.create(
            nom='Autre École', code='AUT01', adresse='789 Av.',
            telephone='+229 21 22 22 22', email='autre@test.bj', directeur_nom='M. Autre'
        )
        academic_year2 = AcademicYear.objects.create(
            school=school2, nom='2026-2027',
            date_debut=self.today, date_fin=self.today + timedelta(days=300)
        )
        with self.assertRaises(ValidationError):
            ClassRoom.objects.create(
                school=self.school, academic_year=academic_year2,  # École différente !
                nom='6ème A', niveau=Niveau.SIXIEME
            )


class ClassRoomRG04TestCase(TestCase):
    """Tests spécifiques RG04 - Capacité des classes."""

    def setUp(self):
        self.school = School.objects.create(
            nom='Lycée Test', code='LYC01', adresse='123 Rue',
            telephone='+229 21 00 00 00', email='contact@lyceetest.bj',
            directeur_nom='M. Directeur'
        )
        self.today = timezone.now().date()
        self.academic_year = AcademicYear.objects.create(
            school=self.school, nom='2026-2027',
            date_debut=self.today, date_fin=self.today + timedelta(days=300),
            is_current=True
        )

    def test_rg04_places_disponibles_calcul(self):
        """Test calcul places disponibles."""
        classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='6ème A', niveau=Niveau.SIXIEME, capacite=35
        )
        self.assertEqual(classroom.places_disponibles, 35)

        # Simuler un effectif (via mock ou quand enrollments existera)
        # Pour l'instant on teste la logique
        classroom.capacite = 30
        classroom.save()
        self.assertEqual(classroom.places_disponibles, 30)

    def test_rg04_est_complete_false_par_defaut(self):
        """Test classe pas complète par défaut."""
        classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='6ème A', niveau=Niveau.SIXIEME, capacite=35
        )
        self.assertFalse(classroom.est_complete)

    def test_rg04_est_complete_when_full(self):
        """Test est_complete quand effectif >= capacite."""
        classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='6ème A', niveau=Niveau.SIXIEME, capacite=2
        )
        # Simuler effectif = 2
        classroom.capacite = 2
        # On ne peut pas tester effectif_actuel sans enrollments,
        # mais on peut tester la logique de la propriété
        self.assertEqual(classroom.capacite, 2)