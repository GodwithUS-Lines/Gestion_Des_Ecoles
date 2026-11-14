from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import date, timedelta

from apps.schools.models import School, AcademicYear


class SchoolModelTestCase(TestCase):
    """Tests pour le modèle School."""

    def setUp(self):
        self.school_data = {
            'nom': 'Lycée Test',
            'code': 'LYC01',
            'adresse': "123 Rue de l'École",
            'telephone': '+229 21 00 00 00',
            'email': 'contact@lyceetest.bj',
            'directeur_nom': 'M. Directeur',
        }

    def test_create_school(self):
        """Test création établissement basique."""
        school = School.objects.create(**self.school_data)
        self.assertEqual(school.nom, 'Lycée Test')
        self.assertEqual(school.code, 'LYC01')
        self.assertTrue(school.is_active)
        self.assertIsNotNone(school.date_creation)

    def test_school_code_unique(self):
        """Test unicité du code établissement (ValidationError via full_clean)."""
        School.objects.create(**self.school_data)
        with self.assertRaises(ValidationError):
            School.objects.create(**{**self.school_data, 'nom': 'Autre Lycée'})

    def test_school_code_uppercase_normalization(self):
        """Test normalisation code en majuscules."""
        school = School.objects.create(**{**self.school_data, 'code': 'lyc01'})
        self.assertEqual(school.code, 'LYC01')

    def test_school_email_lowercase_normalization(self):
        """Test normalisation email en minuscules."""
        school = School.objects.create(**{**self.school_data, 'email': 'CONTACT@LYCEETEST.BJ'})
        self.assertEqual(school.email, 'contact@lyceetest.bj')

    def test_school_str_representation(self):
        """Test représentation string."""
        school = School.objects.create(**self.school_data)
        self.assertEqual(str(school), 'Lycée Test')

    def test_school_soft_delete(self):
        """Test désactivation au lieu de suppression (RG19)."""
        school = School.objects.create(**self.school_data)
        school_pk = school.pk
        school.delete()  # Override delete() -> is_active=False
        school.refresh_from_db()
        self.assertFalse(school.is_active)
        self.assertTrue(School.objects.filter(pk=school_pk).exists())

    def test_school_properties(self):
        """Test propriétés calculées (retournent 0 si relations n'existent pas encore)."""
        school = School.objects.create(**self.school_data)
        self.assertEqual(school.students_count, 0)
        self.assertEqual(school.teachers_count, 0)
        self.assertEqual(school.classrooms_count, 0)
        self.assertIsNone(school.academic_year_current)


class AcademicYearModelTestCase(TestCase):
    """Tests pour le modèle AcademicYear."""

    def setUp(self):
        self.school = School.objects.create(
            nom='Lycée Test',
            code='LYC01',
            adresse="123 Rue de l'École",
            telephone='+229 21 00 00 00',
            email='contact@lyceetest.bj',
            directeur_nom='M. Directeur',
        )
        self.today = timezone.now().date()
        self.year_data = {
            'school': self.school,
            'nom': '2026-2027',
            'date_debut': self.today,
            'date_fin': self.today + timedelta(days=300),
        }

    def test_create_academic_year(self):
        """Test création année scolaire basique."""
        year = AcademicYear.objects.create(**self.year_data)
        self.assertEqual(year.nom, '2026-2027')
        self.assertEqual(year.school, self.school)
        self.assertFalse(year.is_current)
        self.assertTrue(year.is_active)

    def test_academic_year_name_unique_per_school(self):
        """Test unicité du nom par établissement (ValidationError via full_clean)."""
        AcademicYear.objects.create(**self.year_data)
        with self.assertRaises(ValidationError):
            AcademicYear.objects.create(**self.year_data)

    def test_academic_year_same_name_different_schools_ok(self):
        """Test même nom autorisé pour écoles différentes."""
        school2 = School.objects.create(
            nom='Collège Test', code='COL01', adresse='456 Av.',
            telephone='+229 21 11 11 11', email='coll@test.bj', directeur_nom='Mme Directrice'
        )
        AcademicYear.objects.create(**self.year_data)
        year2 = AcademicYear.objects.create(
            school=school2, nom='2026-2027',
            date_debut=self.today, date_fin=self.today + timedelta(days=300)
        )
        self.assertEqual(year2.nom, '2026-2027')

    def test_rg01_unique_current_year_per_school(self):
        """Test RG01 : Une seule année courante par établissement."""
        year1 = AcademicYear.objects.create(**{**self.year_data, 'is_current': True})
        self.assertTrue(year1.is_current)

        # Deuxième année courante pour la même école -> erreur
        with self.assertRaises(ValidationError):
            AcademicYear.objects.create(
                school=self.school,
                nom='2027-2028',
                date_debut=self.today + timedelta(days=365),
                date_fin=self.today + timedelta(days=665),
                is_current=True
            )

    def test_rg01_current_year_different_schools_ok(self):
        """Test RG01 : Années courantes différentes écoles OK."""
        school2 = School.objects.create(
            nom='Collège Test', code='COL01', adresse='456 Av.',
            telephone='+229 21 11 11 11', email='coll@test.bj', directeur_nom='Mme Directrice'
        )
        AcademicYear.objects.create(**{**self.year_data, 'is_current': True})
        year2 = AcademicYear.objects.create(
            school=school2,
            nom='2026-2027',
            date_debut=self.today,
            date_fin=self.today + timedelta(days=300),
            is_current=True
        )
        self.assertTrue(year2.is_current)

    def test_academic_year_date_validation(self):
        """Test validation date_debut < date_fin."""
        with self.assertRaises(ValidationError):
            AcademicYear.objects.create(
                school=self.school,
                nom='2026-2027',
                date_debut=self.today + timedelta(days=10),
                date_fin=self.today,  # date_fin avant date_debut
            )

    def test_academic_year_str_representation(self):
        """Test représentation string."""
        year = AcademicYear.objects.create(**self.year_data)
        self.assertEqual(str(year), f"2026-2027 (Lycée Test)")

    def test_academic_year_soft_delete(self):
        """Test désactivation au lieu de suppression (RG19)."""
        year = AcademicYear.objects.create(**self.year_data)
        year_pk = year.pk
        year.delete()  # Override delete() -> is_active=False
        year.refresh_from_db()
        self.assertFalse(year.is_active)
        self.assertTrue(AcademicYear.objects.filter(pk=year_pk).exists())

    def test_academic_year_is_ongoing_property(self):
        """Test propriété is_ongoing basée sur les dates."""
        # Année en cours
        year_current = AcademicYear.objects.create(
            school=self.school,
            nom='2026-2027',
            date_debut=self.today - timedelta(days=10),
            date_fin=self.today + timedelta(days=300),
        )
        self.assertTrue(year_current.is_ongoing)

        # Année future
        year_future = AcademicYear.objects.create(
            school=self.school,
            nom='2027-2028',
            date_debut=self.today + timedelta(days=365),
            date_fin=self.today + timedelta(days=665),
        )
        self.assertFalse(year_future.is_ongoing)

        # Année passée
        year_past = AcademicYear.objects.create(
            school=self.school,
            nom='2025-2026',
            date_debut=self.today - timedelta(days=700),
            date_fin=self.today - timedelta(days=400),
        )
        self.assertFalse(year_past.is_ongoing)

    def test_school_academic_year_current_property(self):
        """Test propriété school.academic_year_current."""
        # Pas d'année courante
        self.assertIsNone(self.school.academic_year_current)

        # Une année courante
        year = AcademicYear.objects.create(
            **{**self.year_data, 'is_current': True}
        )
        self.assertEqual(self.school.academic_year_current, year)

        # L'année courante désactivée ne doit pas être retournée
        year.is_active = False
        year.save()
        self.assertIsNone(self.school.academic_year_current)


class AcademicYearManagerTestCase(TestCase):
    """Tests pour les méthodes de gestion des années scolaires."""

    def setUp(self):
        self.school = School.objects.create(
            nom='Lycée Test', code='LYC01', adresse='123 Rue',
            telephone='+229 21 00 00 00', email='contact@lyceetest.bj',
            directeur_nom='M. Directeur'
        )
        self.today = timezone.now().date()

    def test_switch_current_year(self):
        """Test basculement année courante - doit désactiver l'ancienne d'abord."""
        year1 = AcademicYear.objects.create(
            school=self.school, nom='2025-2026',
            date_debut=self.today - timedelta(days=400),
            date_fin=self.today - timedelta(days=100),
            is_current=True
        )
        year2 = AcademicYear.objects.create(
            school=self.school, nom='2026-2027',
            date_debut=self.today, date_fin=self.today + timedelta(days=300),
        )

        # Basculer : d'abord désactiver year1, puis activer year2
        year1.is_current = False
        year1.save()
        year2.is_current = True
        year2.save()

        year1.refresh_from_db()
        year2.refresh_from_db()

        self.assertFalse(year1.is_current)
        self.assertTrue(year2.is_current)
        self.assertEqual(self.school.academic_year_current, year2)