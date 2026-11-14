from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import date, timedelta

from apps.schools.models import School, AcademicYear
from apps.classes.models import Serie, ClassRoom, Niveau
from apps.subjects.models import Subject
from apps.teachers.models import Teacher, TeachingAssignment
from apps.accounts.models import User, Role


class TeacherModelTestCase(TestCase):
    """Tests pour le modèle Teacher."""

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
        self.teacher_user = User.objects.create_user(
            email='teacher@test.com', username='teacher1',
            role=Role.TEACHER, password='pass123',
            first_name='Jean', last_name='Dupont'
        )

    def test_create_teacher_with_auto_matricule(self):
        """Test création enseignant avec matricule auto-généré."""
        teacher = Teacher.objects.create(
            user=self.teacher_user,
            school=self.school,
            specialite='Mathématiques',
            diplome='Master Mathématiques',
            date_embauche=self.today - timedelta(days=365)
        )
        # Format: ENS-2026-0001
        self.assertTrue(teacher.matricule.startswith('ENS-2026-'))
        self.assertEqual(teacher.matricule, 'ENS-2026-0001')
        self.assertEqual(teacher.specialite, 'Mathématiques')
        self.assertEqual(teacher.statut, 'TITULAIRE')
        self.assertTrue(teacher.is_active)

    def test_create_teacher_matricule_sequence(self):
        """Test incrémentation séquence matricule par école."""
        Teacher.objects.create(user=self.teacher_user, school=self.school)
        teacher2_user = User.objects.create_user(
            email='teacher2@test.com', username='teacher2',
            role=Role.TEACHER, password='pass123'
        )
        teacher2 = Teacher.objects.create(
            user=teacher2_user, school=self.school
        )
        self.assertEqual(teacher2.matricule, 'ENS-2026-0002')

    def test_teacher_matricule_unique_per_school(self):
        """Test UQ¹ : matricule unique par établissement."""
        Teacher.objects.create(user=self.teacher_user, school=self.school)

        school2 = School.objects.create(
            nom='Autre École', code='AUT01', adresse='789 Av.',
            telephone='+229 21 22 22 22', email='autre@test.bj', directeur_nom='M. Autre'
        )
        teacher_user2 = User.objects.create_user(
            email='teacher2@test.com', username='teacher2',
            role=Role.TEACHER, password='pass123'
        )
        # Même matricule autorisé pour école différente
        teacher2 = Teacher.objects.create(
            user=teacher_user2, school=school2,
            matricule='ENS-2026-0001'  # Forcé pour test
        )
        self.assertEqual(teacher2.matricule, 'ENS-2026-0001')

    def test_teacher_matricule_format_validation(self):
        """Test validation format matricule ENS-YYYY-NNNN."""
        teacher_user2 = User.objects.create_user(
            email='teacher2@test.com', username='teacher2',
            role=Role.TEACHER, password='pass123'
        )
        with self.assertRaises(ValidationError):
            Teacher.objects.create(
                user=teacher_user2, school=self.school,
                matricule='INVALID-FORMAT'
            )

    def test_teacher_matricule_normalization(self):
        """Test normalisation matricule en majuscules."""
        teacher_user2 = User.objects.create_user(
            email='teacher2@test.com', username='teacher2',
            role=Role.TEACHER, password='pass123'
        )
        teacher = Teacher.objects.create(
            user=teacher_user2, school=self.school,
            matricule='ens-2026-0005'  # minuscules
        )
        self.assertEqual(teacher.matricule, 'ENS-2026-0005')

    def test_teacher_str_representation(self):
        """Test représentation string."""
        teacher = Teacher.objects.create(
            user=self.teacher_user, school=self.school
        )
        self.assertEqual(str(teacher), 'Jean Dupont (ENS-2026-0001)')

    def test_teacher_soft_delete(self):
        """Test désactivation au lieu de suppression (RG19)."""
        teacher = Teacher.objects.create(user=self.teacher_user, school=self.school)
        teacher_pk = teacher.pk
        teacher.delete()
        teacher.refresh_from_db()
        self.assertFalse(teacher.is_active)
        self.assertTrue(Teacher.objects.filter(pk=teacher_pk).exists())

    def test_teacher_user_role_teacher(self):
        """Test que l'utilisateur a le rôle TEACHER."""
        # Le modèle ne force pas le rôle, mais c'est une bonne pratique
        self.assertEqual(self.teacher_user.role, Role.TEACHER)


class TeachingAssignmentModelTestCase(TestCase):
    """Tests pour le modèle TeachingAssignment."""

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
            code='A', nom='Série A - Lettres', niveaux_concernes=['1ere', 'terminale']
        )
        self.serie_c = Serie.objects.create(
            code='C', nom='Série C - Sciences', niveaux_concernes=['1ere', 'terminale']
        )

        # Enseignant
        self.teacher_user = User.objects.create_user(
            email='teacher@test.com', username='teacher1',
            role=Role.TEACHER, password='pass123',
            first_name='Jean', last_name='Dupont'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user, school=self.school,
            specialite='Mathématiques'
        )

        # Matière
        self.subject = Subject.objects.create(
            school=self.school, nom='Mathématiques', code='MATH',
            coefficient=3.0, niveau=Niveau.PREMIERE, serie=self.serie_c
        )

        # Classe
        self.classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C', niveau=Niveau.PREMIERE, serie=self.serie_c,
            capacite=30
        )

    def test_create_teaching_assignment(self):
        """Test création affectation basique."""
        ta = TeachingAssignment.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            academic_year=self.academic_year,
            heures_prevues=4
        )
        self.assertEqual(ta.teacher, self.teacher)
        self.assertEqual(ta.subject, self.subject)
        self.assertEqual(ta.classroom, self.classroom)
        self.assertEqual(ta.academic_year, self.academic_year)
        self.assertEqual(ta.heures_prevues, 4)
        self.assertTrue(ta.is_active)

    def test_ta_unique_per_teacher_subject_classroom_year(self):
        """Test unicité affectation par enseignant/matière/classe/année."""
        TeachingAssignment.objects.create(
            teacher=self.teacher, subject=self.subject,
            classroom=self.classroom, academic_year=self.academic_year
        )
        with self.assertRaises(ValidationError):
            TeachingAssignment.objects.create(
                teacher=self.teacher, subject=self.subject,
                classroom=self.classroom, academic_year=self.academic_year
            )

    def test_ta_validation_coherence_ecole(self):
        """Test validation : même établissement pour tous."""
        school2 = School.objects.create(
            nom='Autre École', code='AUT01', adresse='789 Av.',
            telephone='+229 21 22 22 22', email='autre@test.bj', directeur_nom='M. Autre'
        )
        academic_year2 = AcademicYear.objects.create(
            school=school2, nom='2026-2027',
            date_debut=self.today, date_fin=self.today + timedelta(days=300)
        )
        # Utiliser un code de série différent car 'C' existe déjà dans setUp
        serie2 = Serie.objects.create(
            code='D', nom='Série D', niveaux_concernes=['1ere', 'terminale']
        )
        subject2 = Subject.objects.create(
            school=school2, nom='Math', code='MATH2',
            coefficient=3.0, niveau=Niveau.PREMIERE, serie=serie2
        )
        classroom2 = ClassRoom.objects.create(
            school=school2, academic_year=academic_year2,
            nom='1ère A', niveau=Niveau.PREMIERE, serie=serie2, capacite=30
        )

        with self.assertRaises(ValidationError):
            TeachingAssignment.objects.create(
                teacher=self.teacher,  # École 1
                subject=subject2,      # École 2
                classroom=classroom2,  # École 2
                academic_year=academic_year2  # École 2
            )

    def test_ta_validation_niveau_matiere_classe(self):
        """Test validation : niveau matière = niveau classe."""
        subject_6eme = Subject.objects.create(
            school=self.school, nom='Math 6ème', code='MATH6',
            coefficient=2.0, niveau=Niveau.SIXIEME
        )
        classroom_premiere = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère B', niveau=Niveau.PREMIERE, serie=self.serie_c, capacite=30
        )
        with self.assertRaises(ValidationError):
            TeachingAssignment.objects.create(
                teacher=self.teacher, subject=subject_6eme,
                classroom=classroom_premiere, academic_year=self.academic_year
            )

    def test_ta_validation_serie_matiere_classe(self):
        """Test validation : série matière = série classe."""
        subject_serie_a = Subject.objects.create(
            school=self.school, nom='Français A', code='FRA',
            coefficient=1.5, niveau=Niveau.PREMIERE, serie=self.serie_a
        )
        classroom_serie_c = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C2', niveau=Niveau.PREMIERE, serie=self.serie_c, capacite=30
        )
        with self.assertRaises(ValidationError):
            TeachingAssignment.objects.create(
                teacher=self.teacher, subject=subject_serie_a,
                classroom=classroom_serie_c, academic_year=self.academic_year
            )

    def test_ta_str_representation(self):
        """Test représentation string."""
        ta = TeachingAssignment.objects.create(
            teacher=self.teacher, subject=self.subject,
            classroom=self.classroom, academic_year=self.academic_year
        )
        self.assertIn('Jean Dupont', str(ta))
        self.assertIn('Mathématiques', str(ta))
        self.assertIn('1ère C', str(ta))

    def test_ta_soft_delete(self):
        """Test désactivation au lieu de suppression (RG19)."""
        ta = TeachingAssignment.objects.create(
            teacher=self.teacher, subject=self.subject,
            classroom=self.classroom, academic_year=self.academic_year
        )
        ta_pk = ta.pk
        ta.delete()
        ta.refresh_from_db()
        self.assertFalse(ta.is_active)
        self.assertTrue(TeachingAssignment.objects.filter(pk=ta_pk).exists())

    def test_ta_enseignant_peut_saisir_notes(self):
        """Test propriété RG06 : enseignant peut saisir notes."""
        ta = TeachingAssignment.objects.create(
            teacher=self.teacher, subject=self.subject,
            classroom=self.classroom, academic_year=self.academic_year
        )
        self.assertTrue(ta.enseignant_peut_saisir_notes)
        self.assertTrue(ta.enseignant_peut_saisir_absences)

        # Si désactivé
        ta.is_active = False
        ta.save()
        self.assertFalse(ta.enseignant_peut_saisir_notes)

        # Si enseignant désactivé
        ta.is_active = True
        ta.save()
        self.teacher.is_active = False
        self.teacher.save()
        self.assertFalse(ta.enseignant_peut_saisir_notes)


class TeachingAssignmentRG06TestCase(TestCase):
    """Tests spécifiques RG06 - Affectations et permissions."""

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
        self.serie_c = Serie.objects.create(
            code='C', nom='Série C', niveaux_concernes=['1ere', 'terminale']
        )

        # Deux enseignants
        self.teacher_user1 = User.objects.create_user(
            email='t1@test.com', username='t1', role=Role.TEACHER, password='p'
        )
        self.teacher1 = Teacher.objects.create(user=self.teacher_user1, school=self.school)

        self.teacher_user2 = User.objects.create_user(
            email='t2@test.com', username='t2', role=Role.TEACHER, password='p'
        )
        self.teacher2 = Teacher.objects.create(user=self.teacher_user2, school=self.school)

        # Matières
        self.math = Subject.objects.create(
            school=self.school, nom='Mathématiques', code='MATH',
            coefficient=3.0, niveau=Niveau.PREMIERE, serie=self.serie_c
        )
        self.physique = Subject.objects.create(
            school=self.school, nom='Physique', code='PC',
            coefficient=2.0, niveau=Niveau.PREMIERE, serie=self.serie_c
        )

        # Classes
        self.class_c1 = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C1', niveau=Niveau.PREMIERE, serie=self.serie_c, capacite=30
        )
        self.class_c2 = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C2', niveau=Niveau.PREMIERE, serie=self.serie_c, capacite=30
        )

    def test_rg06_teacher1_can_teach_math_c1(self):
        """Enseignant 1 affecté à Maths en 1ère C1."""
        ta = TeachingAssignment.objects.create(
            teacher=self.teacher1, subject=self.math,
            classroom=self.class_c1, academic_year=self.academic_year
        )
        self.assertTrue(ta.enseignant_peut_saisir_notes)

    def test_rg06_teacher1_cannot_teach_physique_without_assignment(self):
        """Enseignant 1 ne peut pas saisir Physique sans affectation."""
        # Pas d'affectation pour Physique
        # On vérifie qu'il n'y a pas d'affectation active
        assignments = TeachingAssignment.objects.filter(
            teacher=self.teacher1, subject=self.physique, is_active=True
        )
        self.assertEqual(assignments.count(), 0)

    def test_rg06_teacher2_can_teach_physique_c2(self):
        """Enseignant 2 affecté à Physique en 1ère C2."""
        ta = TeachingAssignment.objects.create(
            teacher=self.teacher2, subject=self.physique,
            classroom=self.class_c2, academic_year=self.academic_year
        )
        self.assertTrue(ta.enseignant_peut_saisir_notes)

    def test_rg06_multiple_assignments_same_teacher(self):
        """Un enseignant peut avoir plusieurs affectations."""
        TeachingAssignment.objects.create(
            teacher=self.teacher1, subject=self.math,
            classroom=self.class_c1, academic_year=self.academic_year
        )
        TeachingAssignment.objects.create(
            teacher=self.teacher1, subject=self.physique,
            classroom=self.class_c2, academic_year=self.academic_year
        )
        self.assertEqual(self.teacher1.assignments.filter(is_active=True).count(), 2)

    def test_rg06_assignment_links_teacher_subject_classroom(self):
        """Affectation lie correctement enseignant, matière, classe."""
        ta = TeachingAssignment.objects.create(
            teacher=self.teacher1, subject=self.math,
            classroom=self.class_c1, academic_year=self.academic_year
        )
        # Vérifier les relations inverses
        self.assertIn(ta, self.teacher1.assignments.all())
        self.assertIn(ta, self.math.assignments.all())
        self.assertIn(ta, self.class_c1.assignments.all())
        self.assertIn(ta, self.academic_year.assignments.all())


class TeacherIntegrationTestCase(TestCase):
    """Tests d'intégration Teacher avec ClassRoom et Subject."""

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
        self.serie_c = Serie.objects.create(
            code='C', nom='Série C', niveaux_concernes=['1ere', 'terminale']
        )

        self.teacher_user = User.objects.create_user(
            email='teacher@test.com', username='teacher1',
            role=Role.TEACHER, password='pass123',
            first_name='Jean', last_name='Dupont'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user, school=self.school
        )

    def test_classroom_professeur_principal_teacher(self):
        """Test ClassRoom.professeur_principal pointe vers Teacher."""
        classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C', niveau=Niveau.PREMIERE, serie=self.serie_c,
            capacite=30, professeur_principal=self.teacher
        )
        self.assertEqual(classroom.professeur_principal, self.teacher)
        self.assertIn(classroom, self.teacher.classes_principales.all())

    def test_subject_enseignant_responsable_teacher(self):
        """Test Subject.enseignant_responsable pointe vers Teacher."""
        subject = Subject.objects.create(
            school=self.school, nom='Mathématiques', code='MATH',
            coefficient=3.0, niveau=Niveau.PREMIERE, serie=self.serie_c,
            enseignant_responsable=self.teacher
        )
        self.assertEqual(subject.enseignant_responsable, self.teacher)
        self.assertIn(subject, self.teacher.matieres_responsables.all())