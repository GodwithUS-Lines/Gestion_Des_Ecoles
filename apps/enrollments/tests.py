from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta

from apps.schools.models import School, AcademicYear
from apps.classes.models import Serie, ClassRoom, Niveau
from apps.teachers.models import Teacher
from apps.accounts.models import User, Role
from apps.students.models import Parent, Student
from apps.enrollments.models import Enrollment


class EnrollmentModelTestCase(TestCase):
    """Tests pour le modèle Enrollment."""

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
            code='C', nom='Série C - Sciences', niveaux_concernes=['1ere', 'terminale']
        )

        # Parent
        self.parent_user = User.objects.create_user(
            email='parent@test.com', username='parent1',
            role=Role.PARENT, password='pass123',
            first_name='Pierre', last_name='Martin'
        )
        self.parent = Parent.objects.create(user=self.parent_user)

        # Élève
        self.student_user = User.objects.create_user(
            email='student@test.com', username='student1',
            role=Role.STUDENT, password='pass123',
            first_name='Jean', last_name='Dupont'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            school=self.school,
            sexe=Student.Sexe.MASCULIN,
            lieu_naissance='Cotonou',
            parent=self.parent
        )

        # Classe
        self.classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C', niveau=Niveau.PREMIERE, serie=self.serie_c,
            capacite=30
        )

    def test_create_enrollment_auto_numero(self):
        """Test création inscription avec numéro auto-généré."""
        enrollment = Enrollment.objects.create(
            student=self.student,
            classroom=self.classroom,
            academic_year=self.academic_year
        )
        # Format: INS-2026-0001
        self.assertTrue(enrollment.numero_inscription.startswith('INS-2026-'))
        self.assertEqual(enrollment.numero_inscription, 'INS-2026-0001')
        self.assertEqual(enrollment.statut, Enrollment.Statut.ACTIVE)
        self.assertFalse(enrollment.is_reinscription)
        self.assertTrue(enrollment.is_active)

    def test_enrollment_numero_sequence_per_year(self):
        """Test incrémentation séquence numéro inscription par année scolaire."""
        Enrollment.objects.create(
            student=self.student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        student2_user = User.objects.create_user(
            email='student2@test.com', username='student2',
            role=Role.STUDENT, password='pass123'
        )
        student2 = Student.objects.create(
            user=student2_user, school=self.school,
            sexe=Student.Sexe.FEMININ, lieu_naissance='Parakou'
        )
        enrollment2 = Enrollment.objects.create(
            student=student2, classroom=self.classroom,
            academic_year=self.academic_year
        )
        self.assertEqual(enrollment2.numero_inscription, 'INS-2026-0002')

    def test_enrollment_numero_unique_per_year(self):
        """Test RG05 : numéro inscription unique par année scolaire (UQ²)."""
        Enrollment.objects.create(
            student=self.student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        student2_user = User.objects.create_user(
            email='student2@test.com', username='student2',
            role=Role.STUDENT, password='pass123'
        )
        student2 = Student.objects.create(
            user=student2_user, school=self.school,
            sexe=Student.Sexe.FEMININ, lieu_naissance='Parakou'
        )
        # Tenter de forcer le même numéro -> ValidationError
        with self.assertRaises(ValidationError):
            Enrollment.objects.create(
                student=student2, classroom=self.classroom,
                academic_year=self.academic_year,
                numero_inscription='INS-2026-0001'
            )

    def test_enrollment_same_numero_different_years_ok(self):
        """Test même numéro autorisé pour années différentes."""
        academic_year2 = AcademicYear.objects.create(
            school=self.school, nom='2027-2028',
            date_debut=self.today + timedelta(days=365),
            date_fin=self.today + timedelta(days=665)
        )
        classroom2 = ClassRoom.objects.create(
            school=self.school, academic_year=academic_year2,
            nom='1ère C', niveau=Niveau.PREMIERE, serie=self.serie_c,
            capacite=30
        )
        Enrollment.objects.create(
            student=self.student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        student2_user = User.objects.create_user(
            email='student2@test.com', username='student2',
            role=Role.STUDENT, password='pass123'
        )
        student2 = Student.objects.create(
            user=student2_user, school=self.school,
            sexe=Student.Sexe.FEMININ, lieu_naissance='Parakou'
        )
        enrollment2 = Enrollment.objects.create(
            student=student2, classroom=classroom2,
            academic_year=academic_year2,
            numero_inscription='INS-2027-0001'  # Même séquence, année différente
        )
        self.assertEqual(enrollment2.numero_inscription, 'INS-2027-0001')

    def test_rg03_unique_enrollment_per_student_per_year(self):
        """Test RG03 : une seule inscription par élève par année scolaire."""
        Enrollment.objects.create(
            student=self.student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        # Deuxième inscription même élève, même année -> ValidationError
        with self.assertRaises(ValidationError):
            Enrollment.objects.create(
                student=self.student, classroom=self.classroom,
                academic_year=self.academic_year
            )

    def test_rg03_enrollment_different_classroom_same_year_blocked(self):
        """Test RG03 : même élève, même année, classe différente -> bloqué."""
        classroom2 = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère D', niveau=Niveau.PREMIERE, serie=self.serie_c,
            capacite=25
        )
        Enrollment.objects.create(
            student=self.student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        with self.assertRaises(ValidationError):
            Enrollment.objects.create(
                student=self.student, classroom=classroom2,
                academic_year=self.academic_year
            )

    def test_rg04_capacite_classe_respectee(self):
        """Test RG04 : inscription refusée si classe complète."""
        # Remplir la classe avec des noms uniques pour ce test
        for i in range(30):
            user = User.objects.create_user(
                email=f'cap_test_{i}@test.com', username=f'cap_test_{i}',
                role=Role.STUDENT, password='pass123'
            )
            student = Student.objects.create(
                user=user, school=self.school,
                sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
            )
            Enrollment.objects.create(
                student=student, classroom=self.classroom,
                academic_year=self.academic_year
            )
        # Vérifier que la classe est complète
        self.assertTrue(self.classroom.est_complete)
        # 31ème élève -> ValidationError
        user31 = User.objects.create_user(
            email='cap_test_31@test.com', username='cap_test_31',
            role=Role.STUDENT, password='pass123'
        )
        student31 = Student.objects.create(
            user=user31, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
        )
        with self.assertRaises(ValidationError):
            Enrollment.objects.create(
                student=student31, classroom=self.classroom,
                academic_year=self.academic_year
            )

    def test_rg04_annulee_ne_compte_pas_dans_effectif(self):
        """Test : inscriptions annulées ne comptent pas dans l'effectif."""
        # Remplir la classe avec 30 élèves (noms uniques pour ce test)
        for i in range(30):
            user = User.objects.create_user(
                email=f'annul_test_{i}@test.com', username=f'annul_test_{i}',
                role=Role.STUDENT, password='pass123'
            )
            student = Student.objects.create(
                user=user, school=self.school,
                sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
            )
            enrollment = Enrollment.objects.create(
                student=student, classroom=self.classroom,
                academic_year=self.academic_year
            )
            if i == 0:
                enrollment.annuler()  # Annuler le premier

        # La classe a 29 actifs, 1 place dispo
        self.assertEqual(self.classroom.places_disponibles, 1)
        # Nouvel élève peut s'inscrire
        user31 = User.objects.create_user(
            email='annul_test_31@test.com', username='annul_test_31',
            role=Role.STUDENT, password='pass123'
        )
        student31 = Student.objects.create(
            user=user31, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
        )
        enrollment31 = Enrollment.objects.create(
            student=student31, classroom=self.classroom,
            academic_year=self.academic_year
        )
        self.assertEqual(enrollment31.numero_inscription, 'INS-2026-0031')

    def test_enrollment_numero_format_validation(self):
        """Test validation format numéro inscription."""
        student2_user = User.objects.create_user(
            email='student2@test.com', username='student2',
            role=Role.STUDENT, password='pass123'
        )
        student2 = Student.objects.create(
            user=student2_user, school=self.school,
            sexe=Student.Sexe.FEMININ, lieu_naissance='Parakou'
        )
        with self.assertRaises(ValidationError):
            Enrollment.objects.create(
                student=student2, classroom=self.classroom,
                academic_year=self.academic_year,
                numero_inscription='INVALID-FORMAT'
            )

    def test_enrollment_numero_normalization(self):
        """Test normalisation numéro inscription en majuscules."""
        student2_user = User.objects.create_user(
            email='student2@test.com', username='student2',
            role=Role.STUDENT, password='pass123'
        )
        student2 = Student.objects.create(
            user=student2_user, school=self.school,
            sexe=Student.Sexe.FEMININ, lieu_naissance='Parakou'
        )
        enrollment = Enrollment.objects.create(
            student=student2, classroom=self.classroom,
            academic_year=self.academic_year,
            numero_inscription='ins-2026-0005'  # minuscules
        )
        self.assertEqual(enrollment.numero_inscription, 'INS-2026-0005')

    def test_enrollment_str_representation(self):
        """Test représentation string."""
        enrollment = Enrollment.objects.create(
            student=self.student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        self.assertIn('Jean Dupont', str(enrollment))
        self.assertIn('1ère C', str(enrollment))
        self.assertIn('Active', str(enrollment))

    def test_enrollment_soft_delete(self):
        """Test désactivation au lieu de suppression (RG19)."""
        enrollment = Enrollment.objects.create(
            student=self.student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        enrollment_pk = enrollment.pk
        enrollment.delete()
        enrollment.refresh_from_db()
        self.assertFalse(enrollment.is_active)
        self.assertTrue(Enrollment.objects.filter(pk=enrollment_pk).exists())

    def test_enrollment_annuler_method(self):
        """Test méthode annuler()."""
        enrollment = Enrollment.objects.create(
            student=self.student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        enrollment.annuler()
        self.assertEqual(enrollment.statut, Enrollment.Statut.ANNULEE)
        self.assertFalse(enrollment.is_active)

    def test_enrollment_terminer_method(self):
        """Test méthode terminer()."""
        enrollment = Enrollment.objects.create(
            student=self.student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        enrollment.terminer()
        self.assertEqual(enrollment.statut, Enrollment.Statut.TERMINEE)

    def test_enrollment_suspendre_reactiver(self):
        """Test suspendre/réactiver."""
        enrollment = Enrollment.objects.create(
            student=self.student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        enrollment.suspendre()
        self.assertEqual(enrollment.statut, Enrollment.Statut.SUSPENDUE)
        enrollment.reactiver()
        self.assertEqual(enrollment.statut, Enrollment.Statut.ACTIVE)

    def test_enrollment_validation_coherence_ecole(self):
        """Test validation : même établissement pour élève, classe, année."""
        school2 = School.objects.create(
            nom='Autre École', code='AUT01', adresse='789 Av.',
            telephone='+229 21 22 22 22', email='autre@test.bj', directeur_nom='M. Autre'
        )
        academic_year2 = AcademicYear.objects.create(
            school=school2, nom='2026-2027',
            date_debut=self.today, date_fin=self.today + timedelta(days=300)
        )
        # Pour 1ère, une série est obligatoire
        serie2 = Serie.objects.create(
            code='D', nom='Série D', niveaux_concernes=['1ere', 'terminale']
        )
        classroom2 = ClassRoom.objects.create(
            school=school2, academic_year=academic_year2,
            nom='1ère A', niveau=Niveau.PREMIERE, serie=serie2, capacite=30
        )
        with self.assertRaises(ValidationError):
            Enrollment.objects.create(
                student=self.student,  # École 1
                classroom=classroom2,  # École 2
                academic_year=academic_year2  # École 2
            )

    def test_enrollment_validation_classroom_year_match(self):
        """Test validation : classe appartient à l'année scolaire."""
        academic_year2 = AcademicYear.objects.create(
            school=self.school, nom='2027-2028',
            date_debut=self.today + timedelta(days=365),
            date_fin=self.today + timedelta(days=665)
        )
        with self.assertRaises(ValidationError):
            Enrollment.objects.create(
                student=self.student,
                classroom=self.classroom,  # Année 2026-2027
                academic_year=academic_year2  # Année 2027-2028
            )


class EnrollmentReinscriptionTestCase(TestCase):
    """Tests pour la réinscription."""

    def setUp(self):
        self.school = School.objects.create(
            nom='Lycée Test', code='LYC01', adresse='123 Rue',
            telephone='+229 21 00 00 00', email='contact@lyceetest.bj',
            directeur_nom='M. Directeur'
        )
        self.today = timezone.now().date()
        self.academic_year_2025 = AcademicYear.objects.create(
            school=self.school, nom='2025-2026',
            date_debut=self.today - timedelta(days=400),
            date_fin=self.today - timedelta(days=100)
        )
        self.academic_year_2026 = AcademicYear.objects.create(
            school=self.school, nom='2026-2027',
            date_debut=self.today, date_fin=self.today + timedelta(days=300),
            is_current=True
        )
        self.serie_c = Serie.objects.create(
            code='C', nom='Série C', niveaux_concernes=['1ere', 'terminale']
        )

        self.parent_user = User.objects.create_user(
            email='parent@test.com', username='parent1',
            role=Role.PARENT, password='pass123'
        )
        self.parent = Parent.objects.create(user=self.parent_user)

        self.student_user = User.objects.create_user(
            email='student@test.com', username='student1',
            role=Role.STUDENT, password='pass123'
        )
        self.student = Student.objects.create(
            user=self.student_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou',
            parent=self.parent
        )

        self.classroom_2025 = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year_2025,
            nom='6ème A', niveau=Niveau.SIXIEME, capacite=35
        )
        self.classroom_2026 = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year_2026,
            nom='5ème A', niveau=Niveau.CINQUIEME, capacite=35
        )

    def test_reinscription_auto_detected(self):
        """Test détection automatique réinscription."""
        # Inscription année précédente
        Enrollment.objects.create(
            student=self.student, classroom=self.classroom_2025,
            academic_year=self.academic_year_2025
        )
        # Nouvelle inscription -> is_reinscription = True
        enrollment2 = Enrollment.objects.create(
            student=self.student, classroom=self.classroom_2026,
            academic_year=self.academic_year_2026
        )
        self.assertTrue(enrollment2.is_reinscription)

    def test_nouvel_eleve_pas_reinscription(self):
        """Test nouvel élève pas réinscription."""
        enrollment = Enrollment.objects.create(
            student=self.student, classroom=self.classroom_2026,
            academic_year=self.academic_year_2026
        )
        self.assertFalse(enrollment.is_reinscription)

    def test_reinscription_annee_non_terminnee(self):
        """Test réinscription détectée même si année précédente pas terminée."""
        enrollment_prev = Enrollment.objects.create(
            student=self.student, classroom=self.classroom_2025,
            academic_year=self.academic_year_2025,
            statut=Enrollment.Statut.ACTIVE  # Pas terminée
        )
        enrollment2 = Enrollment.objects.create(
            student=self.student, classroom=self.classroom_2026,
            academic_year=self.academic_year_2026
        )
        self.assertTrue(enrollment2.is_reinscription)


class EnrollmentStatutTestCase(TestCase):
    """Tests pour les transitions de statut."""

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

        self.parent_user = User.objects.create_user(
            email='parent@test.com', username='parent1',
            role=Role.PARENT, password='pass123'
        )
        self.parent = Parent.objects.create(user=self.parent_user)

        self.student_user = User.objects.create_user(
            email='student@test.com', username='student1',
            role=Role.STUDENT, password='pass123'
        )
        self.student = Student.objects.create(
            user=self.student_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou',
            parent=self.parent
        )

        self.classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C', niveau=Niveau.PREMIERE, serie=self.serie_c,
            capacite=30
        )

    def test_statut_transitions(self):
        """Test transitions de statut valides."""
        enrollment = Enrollment.objects.create(
            student=self.student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        self.assertEqual(enrollment.statut, Enrollment.Statut.ACTIVE)
        
        enrollment.suspendre()
        self.assertEqual(enrollment.statut, Enrollment.Statut.SUSPENDUE)
        
        enrollment.reactiver()
        self.assertEqual(enrollment.statut, Enrollment.Statut.ACTIVE)
        
        enrollment.terminer()
        self.assertEqual(enrollment.statut, Enrollment.Statut.TERMINEE)
        
        enrollment.annuler()
        self.assertEqual(enrollment.statut, Enrollment.Statut.ANNULEE)

    def test_reactiver_seulement_si_suspendue(self):
        """Test réactiver seulement depuis suspendue."""
        enrollment = Enrollment.objects.create(
            student=self.student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        enrollment.terminer()
        enrollment.reactiver()  # Ne doit pas marcher
        self.assertEqual(enrollment.statut, Enrollment.Statut.TERMINEE)

    def test_est_active_property(self):
        """Test propriété est_active."""
        enrollment = Enrollment.objects.create(
            student=self.student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        self.assertTrue(enrollment.est_active)
        
        enrollment.suspendre()
        self.assertFalse(enrollment.est_active)
        
        enrollment.reactiver()
        self.assertTrue(enrollment.est_active)
        
        enrollment.annuler()
        self.assertFalse(enrollment.est_active)


class EnrollmentRG04ConcurrencyTestCase(TestCase):
    """Tests RG04 - Concurrence et capacité."""

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
        self.classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C', niveau=Niveau.PREMIERE, serie=self.serie_c,
            capacite=2  # Petite capacité pour test
        )

    def test_rg04_inscriptions_sequentielles(self):
        """Test inscriptions séquentielles jusqu'à capacité."""
        for i in range(2):
            user = User.objects.create_user(
                email=f'student{i}@test.com', username=f'student{i}',
                role=Role.STUDENT, password='pass123'
            )
            student = Student.objects.create(
                user=user, school=self.school,
                sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
            )
            enrollment = Enrollment.objects.create(
                student=student, classroom=self.classroom,
                academic_year=self.academic_year
            )
            self.assertTrue(enrollment.pk)

        # 3ème élève -> ValidationError
        user3 = User.objects.create_user(
            email='student3@test.com', username='student3',
            role=Role.STUDENT, password='pass123'
        )
        student3 = Student.objects.create(
            user=user3, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
        )
        with self.assertRaises(ValidationError):
            Enrollment.objects.create(
                student=student3, classroom=self.classroom,
                academic_year=self.academic_year
            )


class EnrollmentIntegrationTestCase(TestCase):
    """Tests d'intégration Enrollment."""

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

        self.parent_user = User.objects.create_user(
            email='parent@test.com', username='parent1',
            role=Role.PARENT, password='pass123'
        )
        self.parent = Parent.objects.create(user=self.parent_user)

    def test_enrollment_list_by_student(self):
        """Test liste inscriptions par élève."""
        student_user = User.objects.create_user(
            email='student@test.com', username='student1',
            role=Role.STUDENT, password='pass123'
        )
        student = Student.objects.create(
            user=student_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou',
            parent=self.parent
        )
        classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C', niveau=Niveau.PREMIERE, serie=self.serie_c,
            capacite=30
        )
        Enrollment.objects.create(
            student=student, classroom=classroom,
            academic_year=self.academic_year
        )
        self.assertEqual(student.enrollments.count(), 1)

    def test_enrollment_list_by_classroom(self):
        """Test liste inscriptions par classe."""
        classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C', niveau=Niveau.PREMIERE, serie=self.serie_c,
            capacite=30
        )
        for i in range(3):
            user = User.objects.create_user(
                email=f'student{i}@test.com', username=f'student{i}',
                role=Role.STUDENT, password='pass123'
            )
            student = Student.objects.create(
                user=user, school=self.school,
                sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou',
                parent=self.parent
            )
            Enrollment.objects.create(
                student=student, classroom=classroom,
                academic_year=self.academic_year
            )
        self.assertEqual(classroom.enrollments.count(), 3)
        self.assertEqual(classroom.effectif_actuel, 3)

    def test_enrollment_list_by_academic_year(self):
        """Test liste inscriptions par année scolaire."""
        classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C', niveau=Niveau.PREMIERE, serie=self.serie_c,
            capacite=30
        )
        for i in range(2):
            user = User.objects.create_user(
                email=f'student{i}@test.com', username=f'student{i}',
                role=Role.STUDENT, password='pass123'
            )
            student = Student.objects.create(
                user=user, school=self.school,
                sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou',
                parent=self.parent
            )
            Enrollment.objects.create(
                student=student, classroom=classroom,
                academic_year=self.academic_year
            )
        self.assertEqual(self.academic_year.enrollments.count(), 2)

    def test_student_inscription_courante(self):
        """Test propriété student.inscription_courante."""
        student_user = User.objects.create_user(
            email='student@test.com', username='student1',
            role=Role.STUDENT, password='pass123'
        )
        student = Student.objects.create(
            user=student_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou',
            parent=self.parent
        )
        classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C', niveau=Niveau.PREMIERE, serie=self.serie_c,
            capacite=30
        )
        enrollment = Enrollment.objects.create(
            student=student, classroom=classroom,
            academic_year=self.academic_year
        )
        self.assertEqual(student.inscription_courante, enrollment)


# ============================================================================
# TESTS DE FORMULAIRES — apps/enrollments
# ============================================================================

class EnrollmentFormTestCase(TestCase):
    """Tests du formulaire EnrollmentForm."""

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
            code='C', nom='Série C - Sciences', niveaux_concernes=['1ere', 'terminale']
        )
        self.parent_user = User.objects.create_user(
            email='parent@test.com', username='parent1',
            role=Role.PARENT, password='pass123'
        )
        self.parent = Parent.objects.create(user=self.parent_user)
        self.student_user = User.objects.create_user(
            email='student@test.com', username='student1',
            role=Role.STUDENT, password='pass123',
            first_name='Jean', last_name='Dupont'
        )
        self.student = Student.objects.create(
            user=self.student_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou',
            parent=self.parent
        )
        self.classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C', niveau=Niveau.PREMIERE, serie=self.serie_c,
            capacite=30
        )

    def test_enrollment_form_valid(self):
        """Test formulaire d'inscription valide."""
        from .forms import EnrollmentForm
        form = EnrollmentForm(data={
            'student': self.student.pk,
            'classroom': self.classroom.pk,
            'academic_year': self.academic_year.pk,
            'statut': 'ACTIVE',
        })
        self.assertTrue(form.is_valid())

    def test_enrollment_form_missing_required(self):
        """Test formulaire d'inscription avec champs requis manquants."""
        from .forms import EnrollmentForm
        form = EnrollmentForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('student', form.errors)
        self.assertIn('classroom', form.errors)
        self.assertIn('academic_year', form.errors)

    def test_enrollment_search_form_empty_valid(self):
        """Test formulaire de recherche d'inscription vide (valide)."""
        from .forms import EnrollmentSearchForm
        form = EnrollmentSearchForm(data={})
        self.assertTrue(form.is_valid())

    def test_enrollment_search_form_with_query(self):
        """Test formulaire de recherche d'inscription avec filtres."""
        from .forms import EnrollmentSearchForm
        form = EnrollmentSearchForm(data={
            'q': 'Dupont',
            'academic_year': self.academic_year.pk,
            'classroom': self.classroom.pk,
            'statut': 'ACTIVE',
        })
        self.assertTrue(form.is_valid())


# ============================================================================
# TESTS DE VUES — apps/enrollments
# ============================================================================

class EnrollmentViewTestCase(TestCase):
    """Tests des vues CRUD inscriptions."""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@test.com', username='admin',
            role=Role.ADMIN, password='pass123',
            first_name='Admin', last_name='User'
        )
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
            code='C', nom='Série C - Sciences', niveaux_concernes=['1ere', 'terminale']
        )
        self.parent_user = User.objects.create_user(
            email='parent@test.com', username='parent1',
            role=Role.PARENT, password='pass123'
        )
        self.parent = Parent.objects.create(user=self.parent_user)
        self.student_user = User.objects.create_user(
            email='student@test.com', username='student1',
            role=Role.STUDENT, password='pass123',
            first_name='Jean', last_name='Dupont'
        )
        self.student = Student.objects.create(
            user=self.student_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou',
            parent=self.parent
        )
        self.classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C', niveau=Niveau.PREMIERE, serie=self.serie_c,
            capacite=30
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        self.client.force_login(self.admin_user)

    def test_enrollment_list_view(self):
        """Test accès à la liste des inscriptions."""
        response = self.client.get(reverse('enrollments:enrollment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.enrollment.numero_inscription)

    def test_enrollment_detail_view(self):
        """Test accès au détail d'une inscription."""
        response = self.client.get(reverse('enrollments:enrollment_detail', args=[self.enrollment.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.enrollment.numero_inscription)
        self.assertContains(response, 'Jean Dupont')

    def test_enrollment_create_view_get(self):
        """Test affichage du formulaire de création d'inscription."""
        response = self.client.get(reverse('enrollments:enrollment_create'))
        self.assertEqual(response.status_code, 200)

    def test_enrollment_create_view_post(self):
        """Test création d'une inscription via le formulaire."""
        student2_user = User.objects.create_user(
            email='student2@test.com', username='student2',
            role=Role.STUDENT, password='pass123',
            first_name='Élève2', last_name='Test'
        )
        student2 = Student.objects.create(
            user=student2_user, school=self.school,
            sexe=Student.Sexe.FEMININ, lieu_naissance='Parakou'
        )
        response = self.client.post(reverse('enrollments:enrollment_create'), {
            'student': student2.pk,
            'classroom': self.classroom.pk,
            'academic_year': self.academic_year.pk,
            'statut': 'ACTIVE',
        })
        self.assertRedirects(response, reverse('enrollments:enrollment_list'))
        self.assertTrue(Enrollment.objects.filter(student=student2).exists())

    def test_enrollment_update_view(self):
        """Test modification d'une inscription."""
        response = self.client.post(reverse('enrollments:enrollment_update', args=[self.enrollment.pk]), {
            'student': self.student.pk,
            'classroom': self.classroom.pk,
            'academic_year': self.academic_year.pk,
            'statut': 'SUSPENDUE',
        })
        self.assertRedirects(response, reverse('enrollments:enrollment_list'))
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.statut, 'SUSPENDUE')

    def test_enrollment_cancel_view(self):
        """Test annulation d'une inscription."""
        response = self.client.post(reverse('enrollments:enrollment_cancel', args=[self.enrollment.pk]))
        self.assertEqual(response.status_code, 302)
        enrollment = Enrollment.objects.get(pk=self.enrollment.pk)
        self.assertEqual(enrollment.statut, Enrollment.Statut.ANNULEE)
        self.assertFalse(enrollment.is_active)

    def test_enrollment_suspend_view(self):
        """Test suspension d'une inscription."""
        response = self.client.post(reverse('enrollments:enrollment_suspend', args=[self.enrollment.pk]))
        self.assertEqual(response.status_code, 302)
        enrollment = Enrollment.objects.get(pk=self.enrollment.pk)
        self.assertEqual(enrollment.statut, Enrollment.Statut.SUSPENDUE)

    def test_enrollment_reactivate_view(self):
        """Test réactivation d'une inscription suspendue."""
        self.enrollment.suspendre()
        response = self.client.post(reverse('enrollments:enrollment_reactivate', args=[self.enrollment.pk]))
        self.assertEqual(response.status_code, 302)
        enrollment = Enrollment.objects.get(pk=self.enrollment.pk)
        self.assertEqual(enrollment.statut, Enrollment.Statut.ACTIVE)

    def test_enrollment_terminate_view(self):
        """Test terminaison d'une inscription."""
        response = self.client.post(reverse('enrollments:enrollment_terminate', args=[self.enrollment.pk]))
        self.assertEqual(response.status_code, 302)
        enrollment = Enrollment.objects.get(pk=self.enrollment.pk)
        self.assertEqual(enrollment.statut, Enrollment.Statut.TERMINEE)


# ============================================================================
# TESTS DE PERMISSIONS — apps/enrollments
# ============================================================================

class EnrollmentPermissionTestCase(TestCase):
    """Tests des contrôles d'accès par rôle sur les vues inscriptions."""

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
        self.student_user = User.objects.create_user(
            email='student@test.com', username='student1',
            role=Role.STUDENT, password='pass123',
            first_name='Jean', last_name='Dupont'
        )
        self.student = Student.objects.create(
            user=self.student_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
        )
        self.classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C', niveau=Niveau.PREMIERE, serie=self.serie_c,
            capacite=30
        )

    def test_admin_can_access_enrollment_list(self):
        """ADMIN peut accéder à la liste des inscriptions."""
        admin = User.objects.create_user(
            email='admin@test.com', username='admin',
            role=Role.ADMIN, password='pass123'
        )
        self.client.force_login(admin)
        response = self.client.get(reverse('enrollments:enrollment_list'))
        self.assertEqual(response.status_code, 200)

    def test_director_can_access_enrollment_list(self):
        """DIRECTOR peut accéder à la liste des inscriptions."""
        director = User.objects.create_user(
            email='director@test.com', username='director',
            role=Role.DIRECTOR, password='pass123'
        )
        self.client.force_login(director)
        response = self.client.get(reverse('enrollments:enrollment_list'))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_enrollment_list(self):
        """Un élève ne peut pas accéder à la liste des inscriptions."""
        self.client.force_login(self.student_user)
        response = self.client.get(reverse('enrollments:enrollment_list'))
        self.assertEqual(response.status_code, 302)

    def test_teacher_cannot_access_enrollment_list(self):
        """Un enseignant ne peut pas accéder à la liste des inscriptions."""
        teacher_user = User.objects.create_user(
            email='teacher@test.com', username='teacher',
            role=Role.TEACHER, password='pass123'
        )
        self.client.force_login(teacher_user)
        response = self.client.get(reverse('enrollments:enrollment_list'))
        self.assertEqual(response.status_code, 302)

    def test_accountant_cannot_access_enrollment_list(self):
        """Un comptable ne peut pas accéder à la liste des inscriptions."""
        accountant_user = User.objects.create_user(
            email='accountant@test.com', username='accountant',
            role=Role.ACCOUNTANT, password='pass123'
        )
        self.client.force_login(accountant_user)
        response = self.client.get(reverse('enrollments:enrollment_list'))
        self.assertEqual(response.status_code, 302)

    def test_parent_cannot_access_enrollment_list(self):
        """Un parent ne peut pas accéder à la liste des inscriptions."""
        parent_user = User.objects.create_user(
            email='parent@test.com', username='parent1',
            role=Role.PARENT, password='pass123'
        )
        self.client.force_login(parent_user)
        response = self.client.get(reverse('enrollments:enrollment_list'))
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_cannot_access_enrollment_list(self):
        """Un utilisateur non connecté est redirigé vers le login."""
        response = self.client.get(reverse('enrollments:enrollment_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login').lstrip('/'), response.url)


# ============================================================================
# TESTS D'INTÉGRATION PARCOURS COMPLET — apps/enrollments
# ============================================================================

class EnrollmentFullIntegrationTestCase(TestCase):
    """Tests d'intégration du parcours complet élève → inscription."""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@test.com', username='admin',
            role=Role.ADMIN, password='pass123',
            first_name='Admin', last_name='User'
        )
        self.client.force_login(self.admin_user)
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
            code='C', nom='Série C - Sciences', niveaux_concernes=['1ere', 'terminale']
        )
        self.classroom = ClassRoom.objects.create(
            school=self.school, academic_year=self.academic_year,
            nom='1ère C', niveau=Niveau.PREMIERE, serie=self.serie_c,
            capacite=2
        )

    def test_parcours_complet_eleve_inscription(self):
        """Parcours complet : créer élève, inscrire, vérifier RG, changer statut."""
        # 1. Créer un élève
        student_user = User.objects.create_user(
            email='eleve@test.com', username='eleve1',
            role=Role.STUDENT, password='pass123',
            first_name='Alice', last_name='Martin'
        )
        student = Student.objects.create(
            user=student_user, school=self.school,
            sexe=Student.Sexe.FEMININ, lieu_naissance='Cotonou'
        )
        # 2. Vérifier le matricule automatique
        self.assertIsNotNone(student.matricule)
        self.assertTrue(student.matricule.startswith('MAT-2026-'))

        # 3. Inscrire l'élève dans une classe
        enrollment = Enrollment.objects.create(
            student=student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        # 4. Vérifier le numéro d'inscription automatique
        self.assertIsNotNone(enrollment.numero_inscription)
        self.assertTrue(enrollment.numero_inscription.startswith('INS-2026-'))
        self.assertEqual(enrollment.statut, Enrollment.Statut.ACTIVE)

        # 5. Vérifier la capacité de la classe (2 places, 1 prise)
        self.assertEqual(self.classroom.places_disponibles, 1)

        # 6. Inscrire un deuxième élève (remplit la classe)
        student2_user = User.objects.create_user(
            email='eleve2@test.com', username='eleve2',
            role=Role.STUDENT, password='pass123',
            first_name='Bob', last_name='Martin'
        )
        student2 = Student.objects.create(
            user=student2_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Parakou'
        )
        enrollment2 = Enrollment.objects.create(
            student=student2, classroom=self.classroom,
            academic_year=self.academic_year
        )
        self.assertTrue(self.classroom.est_complete)

        # 7. Tenter une inscription en doublon (même élève, même année) -> RG03
        with self.assertRaises(ValidationError):
            Enrollment.objects.create(
                student=student, classroom=self.classroom,
                academic_year=self.academic_year
            )

        # 8. Tenter une inscription en dépassant la capacité -> RG04
        student3_user = User.objects.create_user(
            email='eleve3@test.com', username='eleve3',
            role=Role.STUDENT, password='pass123',
            first_name='Carol', last_name='Martin'
        )
        student3 = Student.objects.create(
            user=student3_user, school=self.school,
            sexe=Student.Sexe.FEMININ, lieu_naissance='Porto-Novo'
        )
        with self.assertRaises(ValidationError):
            Enrollment.objects.create(
                student=student3, classroom=self.classroom,
                academic_year=self.academic_year
            )

        # 9. Suspendre l'inscription
        enrollment.suspendre()
        self.assertEqual(enrollment.statut, Enrollment.Statut.SUSPENDUE)
        self.assertFalse(enrollment.est_active)

        # 10. Réactiver l'inscription
        enrollment.reactiver()
        self.assertEqual(enrollment.statut, Enrollment.Statut.ACTIVE)
        self.assertTrue(enrollment.est_active)

        # 11. Terminer l'inscription
        enrollment.terminer()
        self.assertEqual(enrollment.statut, Enrollment.Statut.TERMINEE)
        self.assertFalse(enrollment.est_active)

        # 12. Vérifier la conservation des données (pas de suppression physique)
        self.assertTrue(Enrollment.objects.filter(pk=enrollment.pk).exists())
        self.assertTrue(Student.objects.filter(pk=student.pk).exists())

    def test_parcours_annulation_logique_rg19(self):
        """Test annulation logique (RG19) - données conservées."""
        student_user = User.objects.create_user(
            email='eleve@test.com', username='eleve1',
            role=Role.STUDENT, password='pass123',
            first_name='Alice', last_name='Martin'
        )
        student = Student.objects.create(
            user=student_user, school=self.school,
            sexe=Student.Sexe.FEMININ, lieu_naissance='Cotonou'
        )
        enrollment = Enrollment.objects.create(
            student=student, classroom=self.classroom,
            academic_year=self.academic_year
        )
        enrollment_pk = enrollment.pk
        # Annulation logique
        enrollment.annuler()
        self.assertEqual(enrollment.statut, Enrollment.Statut.ANNULEE)
        self.assertFalse(enrollment.is_active)
        # Données conservées
        self.assertTrue(Enrollment.objects.filter(pk=enrollment_pk).exists())
        enrollment.refresh_from_db()
        self.assertFalse(enrollment.is_active)