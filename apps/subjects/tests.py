from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import date, timedelta

from apps.schools.models import School, AcademicYear
from apps.classes.models import Serie, ClassRoom, Niveau
from apps.teachers.models import Teacher
from apps.accounts.models import User, Role
from apps.subjects.models import Subject


class SubjectModelTestCase(TestCase):
    """Tests pour le modèle Subject."""

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
        # Créer des séries
        self.serie_a = Serie.objects.create(
            code='A', nom='Série A - Lettres', niveaux_concernes=['1ere', 'terminale']
        )
        self.serie_c = Serie.objects.create(
            code='C', nom='Série C - Sciences', niveaux_concernes=['1ere', 'terminale']
        )
        # Créer un utilisateur enseignant
        self.teacher_user = User.objects.create_user(
            email='teacher@test.com', username='teacher1',
            role=Role.TEACHER, password='pass123',
            first_name='Jean', last_name='Dupont'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user, school=self.school,
            matricule='ENS-2026-0001', specialite='Mathématiques'
        )

    def test_create_subject_college(self):
        """Test création matière collège (sans série)."""
        subject = Subject.objects.create(
            school=self.school,
            nom='Mathématiques',
            code='MATH',
            coefficient=2.0,
            niveau=Niveau.SIXIEME
        )
        self.assertEqual(subject.nom, 'Mathématiques')
        self.assertEqual(subject.code, 'MATH')
        self.assertEqual(subject.coefficient, 2.0)
        self.assertEqual(subject.niveau, Niveau.SIXIEME)
        self.assertIsNone(subject.serie)
        self.assertIsNone(subject.enseignant_responsable)
        self.assertTrue(subject.is_active)
        self.assertTrue(subject.niveau_est_college)
        self.assertFalse(subject.niveau_est_lycee)

    def test_create_subject_lycee_avec_serie(self):
        """Test création matière lycée avec série."""
        subject = Subject.objects.create(
            school=self.school,
            nom='Mathématiques Spéciales',
            code='MATHS',
            coefficient=3.0,
            niveau=Niveau.PREMIERE,
            serie=self.serie_c
        )
        self.assertEqual(subject.niveau, Niveau.PREMIERE)
        self.assertEqual(subject.serie, self.serie_c)
        self.assertTrue(subject.niveau_est_lycee)

    def test_create_subject_lycee_sans_serie(self):
        """Test création matière 2nde sans série (2nde n'a pas de série)."""
        subject = Subject.objects.create(
            school=self.school,
            nom='Physique-Chimie',
            code='PC',
            coefficient=1.5,
            niveau=Niveau.SECONDE
        )
        self.assertEqual(subject.niveau, Niveau.SECONDE)
        self.assertIsNone(subject.serie)
        self.assertTrue(subject.niveau_est_lycee)

    def test_subject_code_unique_per_school(self):
        """Test UQ¹ : code unique par établissement."""
        Subject.objects.create(
            school=self.school, nom='Mathématiques', code='MATH',
            coefficient=2.0, niveau=Niveau.SIXIEME
        )
        with self.assertRaises(ValidationError):
            Subject.objects.create(
                school=self.school, nom='Autre Math', code='MATH',
                coefficient=1.0, niveau=Niveau.CINQUIEME
            )

    def test_subject_same_code_different_schools_ok(self):
        """Test même code autorisé pour écoles différentes."""
        school2 = School.objects.create(
            nom='Collège Test', code='COL01', adresse='456 Av.',
            telephone='+229 21 11 11 11', email='coll@test.bj', directeur_nom='Mme Directrice'
        )
        Subject.objects.create(
            school=self.school, nom='Mathématiques', code='MATH',
            coefficient=2.0, niveau=Niveau.SIXIEME
        )
        subject2 = Subject.objects.create(
            school=school2, nom='Mathématiques', code='MATH',
            coefficient=2.0, niveau=Niveau.SIXIEME
        )
        self.assertEqual(subject2.code, 'MATH')

    def test_subject_coefficient_validation(self):
        """Test validation coefficient > 0."""
        with self.assertRaises(ValidationError):
            Subject.objects.create(
                school=self.school, nom='Test', code='TEST',
                coefficient=0, niveau=Niveau.SIXIEME
            )

        with self.assertRaises(ValidationError):
            Subject.objects.create(
                school=self.school, nom='Test', code='TEST2',
                coefficient=-1.0, niveau=Niveau.SIXIEME
            )

    def test_subject_code_uppercase_normalization(self):
        """Test normalisation code en majuscules."""
        subject = Subject.objects.create(
            school=self.school, nom='Test', code='math',
            coefficient=1.0, niveau=Niveau.SIXIEME
        )
        self.assertEqual(subject.code, 'MATH')

    def test_subject_str_representation(self):
        """Test représentation string."""
        subject = Subject.objects.create(
            school=self.school, nom='Français', code='FR',
            coefficient=1.5, niveau=Niveau.CINQUIEME
        )
        self.assertIn('Français', str(subject))
        self.assertIn('FR', str(subject))
        self.assertIn('5ème', str(subject))

    def test_subject_soft_delete(self):
        """Test désactivation au lieu de suppression (RG19)."""
        subject = Subject.objects.create(
            school=self.school, nom='Test', code='TEST',
            coefficient=1.0, niveau=Niveau.SIXIEME
        )
        subject_pk = subject.pk
        subject.delete()
        subject.refresh_from_db()
        self.assertFalse(subject.is_active)
        self.assertTrue(Subject.objects.filter(pk=subject_pk).exists())

    def test_subject_validation_serie_pas_pour_college(self):
        """Test pas de série pour collège."""
        with self.assertRaises(ValidationError):
            Subject.objects.create(
                school=self.school, nom='Test', code='TEST',
                coefficient=1.0, niveau=Niveau.SIXIEME, serie=self.serie_a
            )

    def test_subject_validation_serie_pas_pour_seconde(self):
        """Test pas de série pour 2nde."""
        with self.assertRaises(ValidationError):
            Subject.objects.create(
                school=self.school, nom='Test', code='TEST',
                coefficient=1.0, niveau=Niveau.SECONDE, serie=self.serie_a
            )

    def test_subject_validation_serie_optional_pour_premiere(self):
        """Test série optionnelle pour 1ère."""
        # Sans série - OK
        subject1 = Subject.objects.create(
            school=self.school, nom='Français', code='FR1',
            coefficient=1.5, niveau=Niveau.PREMIERE
        )
        self.assertIsNone(subject1.serie)

        # Avec série - OK
        subject2 = Subject.objects.create(
            school=self.school, nom='Mathématiques', code='MATH1',
            coefficient=3.0, niveau=Niveau.PREMIERE, serie=self.serie_a
        )
        self.assertEqual(subject2.serie, self.serie_a)

    def test_subject_validation_serie_correspond_niveau(self):
        """Test série correspond au niveau."""
        # Créer une série qui ne concerne que 1ère
        serie_1ere_only = Serie.objects.create(
            code='X', nom='Série X - 1ère seulement', niveaux_concernes=['1ere']
        )
        with self.assertRaises(ValidationError):
            Subject.objects.create(
                school=self.school, nom='Test', code='TEST',
                coefficient=1.0, niveau=Niveau.TERMINALE, serie=serie_1ere_only
            )

    def test_subject_enseignant_responsable_meme_ecole(self):
        """Test enseignant responsable même école."""
        school2 = School.objects.create(
            nom='Autre École', code='AUT01', adresse='789 Av.',
            telephone='+229 21 22 22 22', email='autre@test.bj', directeur_nom='M. Autre'
        )
        teacher_user2 = User.objects.create_user(
            email='teacher2@test.com', username='teacher2',
            role=Role.TEACHER, password='pass123'
        )
        teacher2 = Teacher.objects.create(
            user=teacher_user2, school=school2, matricule='ENS-2026-0002'
        )
        with self.assertRaises(ValidationError):
            Subject.objects.create(
                school=self.school, nom='Test', code='TEST',
                coefficient=1.0, niveau=Niveau.SIXIEME,
                enseignant_responsable=teacher2  # École différente !
            )

    def test_subject_enseignant_responsable_optionnel(self):
        """Test enseignant responsable optionnel."""
        subject = Subject.objects.create(
            school=self.school, nom='Test', code='TEST',
            coefficient=1.0, niveau=Niveau.SIXIEME
        )
        self.assertIsNone(subject.enseignant_responsable)

        subject2 = Subject.objects.create(
            school=self.school, nom='Test2', code='TEST2',
            coefficient=1.0, niveau=Niveau.SIXIEME,
            enseignant_responsable=self.teacher
        )
        self.assertEqual(subject2.enseignant_responsable, self.teacher)


class SubjectIntegrationTestCase(TestCase):
    """Tests d'intégration Subject avec autres modèles."""

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
        self.serie_a = Serie.objects.create(
            code='A', nom='Série A', niveaux_concernes=['1ere', 'terminale']
        )

    def test_subject_list_by_school(self):
        """Test liste matières par école."""
        Subject.objects.create(school=self.school, nom='Math', code='MATH', coefficient=2.0, niveau=Niveau.SIXIEME)
        Subject.objects.create(school=self.school, nom='Français', code='FR', coefficient=1.5, niveau=Niveau.SIXIEME)
        Subject.objects.create(school=self.school, nom='Physique', code='PC', coefficient=2.0, niveau=Niveau.PREMIERE)

        self.assertEqual(self.school.subjects.count(), 3)
        self.assertEqual(self.school.subjects.filter(niveau=Niveau.SIXIEME).count(), 2)
        self.assertEqual(self.school.subjects.filter(niveau=Niveau.PREMIERE).count(), 1)

    def test_subject_list_by_niveau(self):
        """Test liste matières par niveau."""
        Subject.objects.create(school=self.school, nom='Math', code='MATH', coefficient=2.0, niveau=Niveau.SIXIEME)
        Subject.objects.create(school=self.school, nom='Français', code='FR', coefficient=1.5, niveau=Niveau.SIXIEME)
        Subject.objects.create(school=self.school, nom='Physique', code='PC', coefficient=2.0, niveau=Niveau.PREMIERE, serie=self.serie_a)

        sixieme_subjects = Subject.objects.filter(school=self.school, niveau=Niveau.SIXIEME)
        self.assertEqual(sixieme_subjects.count(), 2)

        premiere_subjects = Subject.objects.filter(school=self.school, niveau=Niveau.PREMIERE)
        self.assertEqual(premiere_subjects.count(), 1)
        self.assertEqual(premiere_subjects.first().serie, self.serie_a)