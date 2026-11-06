from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor

from apps.schools.models import School, AcademicYear
from apps.classes.models import Serie, ClassRoom, Niveau
from apps.teachers.models import Teacher
from apps.accounts.models import User, Role
from apps.students.models import Parent, Student


class ParentModelTestCase(TestCase):
    """Tests pour le modèle Parent."""

    def setUp(self):
        self.school = School.objects.create(
            nom='Lycée Test', code='LYC01', adresse='123 Rue',
            telephone='+229 21 00 00 00', email='contact@lyceetest.bj',
            directeur_nom='M. Directeur'
        )
        self.parent_user = User.objects.create_user(
            email='parent@test.com', username='parent1',
            role=Role.PARENT, password='pass123',
            first_name='Pierre', last_name='Martin'
        )

    def test_create_parent(self):
        """Test création parent basique."""
        parent = Parent.objects.create(
            user=self.parent_user,
            profession='Ingénieur',
            revenu_mensuel=500000
        )
        self.assertEqual(parent.user, self.parent_user)
        self.assertEqual(parent.profession, 'Ingénieur')
        self.assertEqual(parent.revenu_mensuel, 500000)
        self.assertTrue(parent.is_active)

    def test_parent_user_role_parent(self):
        """Test que l'utilisateur a le rôle PARENT."""
        self.assertEqual(self.parent_user.role, Role.PARENT)

    def test_parent_validation_user_role(self):
        """Test validation : user doit avoir rôle PARENT."""
        wrong_user = User.objects.create_user(
            email='wrong@test.com', username='wrong',
            role=Role.STUDENT, password='pass123'
        )
        with self.assertRaises(ValidationError):
            Parent.objects.create(user=wrong_user)

    def test_parent_str_representation(self):
        """Test représentation string."""
        parent = Parent.objects.create(user=self.parent_user)
        self.assertEqual(str(parent), 'Pierre Martin')

    def test_parent_soft_delete(self):
        """Test désactivation au lieu de suppression (RG19)."""
        parent = Parent.objects.create(user=self.parent_user)
        parent_pk = parent.pk
        parent.delete()
        parent.refresh_from_db()
        self.assertFalse(parent.is_active)
        self.assertTrue(Parent.objects.filter(pk=parent_pk).exists())

    def test_parent_enfants_relation(self):
        """Test relation inverse vers enfants (Student)."""
        parent = Parent.objects.create(user=self.parent_user)
        self.assertEqual(parent.enfants.count(), 0)


class StudentModelTestCase(TestCase):
    """Tests pour le modèle Student."""

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

        self.student_user = User.objects.create_user(
            email='student@test.com', username='student1',
            role=Role.STUDENT, password='pass123',
            first_name='Jean', last_name='Dupont'
        )

        self.parent_user = User.objects.create_user(
            email='parent@test.com', username='parent1',
            role=Role.PARENT, password='pass123',
            first_name='Pierre', last_name='Martin'
        )
        self.parent = Parent.objects.create(user=self.parent_user)

    def test_create_student_with_auto_matricule(self):
        """Test création élève avec matricule auto-généré."""
        student = Student.objects.create(
            user=self.student_user,
            school=self.school,
            sexe=Student.Sexe.MASCULIN,
            lieu_naissance='Cotonou',
            parent=self.parent
        )
        # Format: MAT-2026-0001
        self.assertTrue(student.matricule.startswith('MAT-2026-'))
        self.assertEqual(student.matricule, 'MAT-2026-0001')
        self.assertEqual(student.sexe, Student.Sexe.MASCULIN)
        self.assertEqual(student.lieu_naissance, 'Cotonou')
        self.assertEqual(student.nationalite, 'Béninoise')
        self.assertEqual(student.parent, self.parent)
        self.assertTrue(student.is_active)

    def test_student_matricule_sequence_per_school(self):
        """Test incrémentation séquence matricule par établissement."""
        Student.objects.create(
            user=self.student_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
        )
        student2_user = User.objects.create_user(
            email='student2@test.com', username='student2',
            role=Role.STUDENT, password='pass123'
        )
        student2 = Student.objects.create(
            user=student2_user, school=self.school,
            sexe=Student.Sexe.FEMININ, lieu_naissance='Porto-Novo'
        )
        self.assertEqual(student2.matricule, 'MAT-2026-0002')

    def test_student_matricule_unique_per_school(self):
        """Test RG02 : matricule unique par établissement."""
        Student.objects.create(
            user=self.student_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
        )

        school2 = School.objects.create(
            nom='Autre École', code='AUT01', adresse='789 Av.',
            telephone='+229 21 22 22 22', email='autre@test.bj', directeur_nom='M. Autre'
        )
        student2_user = User.objects.create_user(
            email='student2@test.com', username='student2',
            role=Role.STUDENT, password='pass123'
        )
        # Même matricule autorisé pour école différente
        student2 = Student.objects.create(
            user=student2_user, school=school2,
            sexe=Student.Sexe.FEMININ, lieu_naissance='Parakou',
            matricule='MAT-2026-0001'  # Forcé pour test
        )
        self.assertEqual(student2.matricule, 'MAT-2026-0001')

    def test_student_matricule_format_validation(self):
        """Test validation format matricule MAT-YYYY-NNNN."""
        student_user2 = User.objects.create_user(
            email='student2@test.com', username='student2',
            role=Role.STUDENT, password='pass123'
        )
        with self.assertRaises(ValidationError):
            Student.objects.create(
                user=student_user2, school=self.school,
                sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou',
                matricule='INVALID-FORMAT'
            )

    def test_student_matricule_normalization(self):
        """Test normalisation matricule en majuscules."""
        student_user2 = User.objects.create_user(
            email='student2@test.com', username='student2',
            role=Role.STUDENT, password='pass123'
        )
        student = Student.objects.create(
            user=student_user2, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou',
            matricule='mat-2026-0005'  # minuscules
        )
        self.assertEqual(student.matricule, 'MAT-2026-0005')

    def test_student_str_representation(self):
        """Test représentation string."""
        student = Student.objects.create(
            user=self.student_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
        )
        self.assertEqual(str(student), 'Jean Dupont (MAT-2026-0001)')

    def test_student_soft_delete(self):
        """Test désactivation au lieu de suppression (RG19)."""
        student = Student.objects.create(
            user=self.student_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
        )
        student_pk = student.pk
        student.delete()
        student.refresh_from_db()
        self.assertFalse(student.is_active)
        self.assertTrue(Student.objects.filter(pk=student_pk).exists())

    def test_student_user_role_student(self):
        """Test que l'utilisateur a le rôle STUDENT."""
        self.assertEqual(self.student_user.role, Role.STUDENT)

    def test_student_validation_user_role(self):
        """Test validation : user doit avoir rôle STUDENT."""
        wrong_user = User.objects.create_user(
            email='wrong@test.com', username='wrong',
            role=Role.PARENT, password='pass123'
        )
        with self.assertRaises(ValidationError):
            Student.objects.create(
                user=wrong_user, school=self.school,
                sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
            )

    def test_student_parent_optional(self):
        """Test parent optionnel."""
        student = Student.objects.create(
            user=self.student_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
        )
        self.assertIsNone(student.parent)

        student2_user = User.objects.create_user(
            email='student2@test.com', username='student2',
            role=Role.STUDENT, password='pass123'
        )
        student2 = Student.objects.create(
            user=student2_user, school=self.school,
            sexe=Student.Sexe.FEMININ, lieu_naissance='Parakou',
            parent=self.parent
        )
        self.assertEqual(student2.parent, self.parent)

    def test_student_parent_must_be_active(self):
        """Test parent doit être actif."""
        self.parent.is_active = False
        self.parent.save()
        student_user2 = User.objects.create_user(
            email='student2@test.com', username='student2',
            role=Role.STUDENT, password='pass123'
        )
        # La validation doit échouer car parent n'est pas actif
        with self.assertRaises(ValidationError):
            Student.objects.create(
                user=student_user2, school=self.school,
                sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou',
                parent=self.parent
            )


class StudentMatriculeConcurrencyTestCase(TestCase):
    """Tests de concurrence pour la génération de matricule (RG02)."""

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

    def create_student(self, index):
        """Crée un élève dans une transaction séparée."""
        user = User.objects.create_user(
            email=f'student{index}@test.com',
            username=f'student{index}',
            role=Role.STUDENT,
            password='pass123'
        )
        student = Student.objects.create(
            user=user,
            school=self.school,
            sexe=Student.Sexe.MASCULIN,
            lieu_naissance='Cotonou'
        )
        return student.matricule

    def test_concurrent_matricule_generation(self):
        """Test génération matricule en concurrence (simulation)."""
        # Créer plusieurs étudiants séquentiellement (simulation de concurrence)
        matricules = []
        for i in range(5):
            matricule = self.create_student(i)
            matricules.append(matricule)

        # Vérifier que tous les matricules sont uniques et séquentiels
        self.assertEqual(len(set(matricules)), 5)  # Tous uniques
        self.assertEqual(matricules, [
            'MAT-2026-0001', 'MAT-2026-0002', 'MAT-2026-0003',
            'MAT-2026-0004', 'MAT-2026-0005'
        ])


class StudentIntegrationTestCase(TestCase):
    """Tests d'intégration Student avec autres modèles."""

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

        self.parent_user = User.objects.create_user(
            email='parent@test.com', username='parent1',
            role=Role.PARENT, password='pass123',
            first_name='Pierre', last_name='Martin'
        )
        self.parent = Parent.objects.create(user=self.parent_user)

    def test_student_list_by_school(self):
        """Test liste élèves par école."""
        for i in range(3):
            user = User.objects.create_user(
                email=f'student{i}@test.com', username=f'student{i}',
                role=Role.STUDENT, password='pass123'
            )
            Student.objects.create(
                user=user, school=self.school,
                sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou',
                parent=self.parent if i == 0 else None
            )

        self.assertEqual(self.school.students.count(), 3)
        self.assertEqual(self.school.students.filter(is_active=True).count(), 3)

    def test_parent_enfants_relation(self):
        """Test relation Parent -> enfants (Student)."""
        for i in range(2):
            user = User.objects.create_user(
                email=f'student{i}@test.com', username=f'student{i}',
                role=Role.STUDENT, password='pass123'
            )
            Student.objects.create(
                user=user, school=self.school,
                sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou',
                parent=self.parent
            )

        self.assertEqual(self.parent.enfants.count(), 2)
        self.assertEqual(self.parent.enfants.filter(is_active=True).count(), 2)

    def test_student_inscription_courante_property(self):
        """Test propriété inscription_courante (retourne None si pas d'enrollments)."""
        student_user = User.objects.create_user(
            email='student@test.com', username='student1',
            role=Role.STUDENT, password='pass123'
        )
        student = Student.objects.create(
            user=student_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
        )
        self.assertIsNone(student.inscription_courante)

    def test_student_user_onetoone(self):
        """Test relation OneToOne User -> Student."""
        student_user = User.objects.create_user(
            email='student@test.com', username='student1',
            role=Role.STUDENT, password='pass123'
        )
        student = Student.objects.create(
            user=student_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
        )
        # Accès inverse
        self.assertEqual(student_user.student_profile, student)


class StudentRG02TestCase(TestCase):
    """Tests spécifiques RG02 - Matricule unique par établissement."""

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

    def test_rg02_matricule_auto_generated(self):
        """Test RG02 : matricule généré automatiquement."""
        user = User.objects.create_user(
            email='student@test.com', username='student1',
            role=Role.STUDENT, password='pass123'
        )
        student = Student.objects.create(
            user=user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
        )
        self.assertIsNotNone(student.matricule)
        self.assertTrue(student.matricule.startswith('MAT-2026-'))

    def test_rg02_matricule_unique_constraint_db(self):
        """Test RG02 : contrainte DB d'unicité par établissement (ValidationError via full_clean)."""
        user1 = User.objects.create_user(
            email='student1@test.com', username='student1',
            role=Role.STUDENT, password='pass123'
        )
        Student.objects.create(
            user=user1, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
        )
        user2 = User.objects.create_user(
            email='student2@test.com', username='student2',
            role=Role.STUDENT, password='pass123'
        )
        # Tenter de forcer le même matricule -> ValidationError via full_clean (avant DB)
        with self.assertRaises(ValidationError):
            Student.objects.create(
                user=user2, school=self.school,
                sexe=Student.Sexe.FEMININ, lieu_naissance='Parakou',
                matricule='MAT-2026-0001'  # Forcé manuellement
            )

    def test_rg02_matricule_same_ok_different_schools(self):
        """Test RG02 : même matricule OK pour écoles différentes."""
        school2 = School.objects.create(
            nom='Autre École', code='AUT01', adresse='789 Av.',
            telephone='+229 21 22 22 22', email='autre@test.bj', directeur_nom='M. Autre'
        )
        user1 = User.objects.create_user(
            email='student1@test.com', username='student1',
            role=Role.STUDENT, password='pass123'
        )
        Student.objects.create(
            user=user1, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
        )
        user2 = User.objects.create_user(
            email='student2@test.com', username='student2',
            role=Role.STUDENT, password='pass123'
        )
        student2 = Student.objects.create(
            user=user2, school=school2,
            sexe=Student.Sexe.FEMININ, lieu_naissance='Parakou',
            matricule='MAT-2026-0001'  # Même matricule, école différente
        )
        self.assertEqual(student2.matricule, 'MAT-2026-0001')


class StudentRG19TestCase(TestCase):
    """Tests spécifiques RG19 - Pas de suppression physique."""

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
        self.student_user = User.objects.create_user(
            email='student@test.com', username='student1',
            role=Role.STUDENT, password='pass123'
        )

    def test_rg19_student_soft_delete(self):
        """Test RG19 : Student soft delete."""
        student = Student.objects.create(
            user=self.student_user, school=self.school,
            sexe=Student.Sexe.MASCULIN, lieu_naissance='Cotonou'
        )
        student_pk = student.pk
        student.delete()
        student.refresh_from_db()
        self.assertFalse(student.is_active)
        self.assertTrue(Student.objects.filter(pk=student_pk).exists())

    def test_rg19_parent_soft_delete(self):
        """Test RG19 : Parent soft delete."""
        parent_user = User.objects.create_user(
            email='parent@test.com', username='parent1',
            role=Role.PARENT, password='pass123'
        )
        parent = Parent.objects.create(user=parent_user)
        parent_pk = parent.pk
        parent.delete()
        parent.refresh_from_db()
        self.assertFalse(parent.is_active)
        self.assertTrue(Parent.objects.filter(pk=parent_pk).exists())


# ============================================================================
# TESTS DE FORMULAIRES — apps/students
# ============================================================================

class StudentFormTestCase(TestCase):
    """Tests du formulaire StudentForm."""

    def setUp(self):
        self.school = School.objects.create(
            nom='Lycée Test', code='LYC01', adresse='123 Rue',
            telephone='+229 21 00 00 00', email='contact@lyceetest.bj',
            directeur_nom='M. Directeur'
        )
        self.student_user = User.objects.create_user(
            email='student@test.com', username='student1',
            role=Role.STUDENT, password='pass123',
            first_name='Jean', last_name='Dupont'
        )
        self.parent_user = User.objects.create_user(
            email='parent@test.com', username='parent1',
            role=Role.PARENT, password='pass123',
            first_name='Pierre', last_name='Martin'
        )
        self.parent = Parent.objects.create(user=self.parent_user)

    def test_student_form_valid(self):
        """Test formulaire étudiant valide."""
        from .forms import StudentForm
        form = StudentForm(data={
            'user': self.student_user.pk,
            'school': self.school.pk,
            'sexe': 'M',
            'lieu_naissance': 'Cotonou',
            'nationalite': 'Béninoise',
            'parent': self.parent.pk,
        })
        self.assertTrue(form.is_valid())

    def test_student_form_missing_required_fields(self):
        """Test formulaire étudiant avec champs requis manquants."""
        from .forms import StudentForm
        form = StudentForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('user', form.errors)
        self.assertIn('school', form.errors)
        self.assertIn('sexe', form.errors)
        self.assertIn('lieu_naissance', form.errors)

    def test_student_form_invalid_user_role(self):
        """Test formulaire étudiant avec utilisateur non-STUDENT."""
        from .forms import StudentForm
        wrong_user = User.objects.create_user(
            email='wrong@test.com', username='wrong',
            role=Role.TEACHER, password='pass123'
        )
        form = StudentForm(data={
            'user': wrong_user.pk,
            'school': self.school.pk,
            'sexe': 'M',
            'lieu_naissance': 'Cotonou',
        })
        self.assertFalse(form.is_valid())

    def test_parent_form_valid(self):
        """Test formulaire parent valide."""
        from .forms import ParentForm
        new_parent_user = User.objects.create_user(
            email='newparent@test.com', username='newparent',
            role=Role.PARENT, password='pass123',
            first_name='Nouveau', last_name='Parent'
        )
        form = ParentForm(data={
            'user': new_parent_user.pk,
            'profession': 'Ingénieur',
            'revenu_mensuel': '500000.00',
        })
        self.assertTrue(form.is_valid())

    def test_parent_form_invalid_user_role(self):
        """Test formulaire parent avec utilisateur non-PARENT."""
        from .forms import ParentForm
        wrong_user = User.objects.create_user(
            email='wrong@test.com', username='wrong2',
            role=Role.STUDENT, password='pass123'
        )
        form = ParentForm(data={
            'user': wrong_user.pk,
            'profession': 'Ingénieur',
        })
        self.assertFalse(form.is_valid())


class StudentSearchFormTestCase(TestCase):
    """Tests du formulaire StudentSearchForm."""

    def setUp(self):
        self.school = School.objects.create(
            nom='Lycée Test', code='LYC01', adresse='123 Rue',
            telephone='+229 21 00 00 00', email='contact@lyceetest.bj',
            directeur_nom='M. Directeur'
        )

    def test_student_search_form_empty_valid(self):
        """Test formulaire de recherche vide (valide)."""
        from .forms import StudentSearchForm
        form = StudentSearchForm(data={})
        self.assertTrue(form.is_valid())

    def test_student_search_form_with_query(self):
        """Test formulaire de recherche avec un terme."""
        from .forms import StudentSearchForm
        form = StudentSearchForm(data={
            'q': 'Dupont',
            'school': self.school.pk,
            'is_active': 'True',
        })
        self.assertTrue(form.is_valid())


# ============================================================================
# TESTS DE VUES — apps/students
# ============================================================================

class StudentViewTestCase(TestCase):
    """Tests des vues CRUD étudiants."""

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
        )
        self.client.force_login(self.admin_user)

    def test_student_list_view(self):
        """Test accès à la liste des élèves."""
        response = self.client.get(reverse('students:student_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jean Dupont')

    def test_student_detail_view(self):
        """Test accès au détail d'un élève."""
        response = self.client.get(reverse('students:student_detail', args=[self.student.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jean Dupont')
        self.assertContains(response, self.student.matricule)

    def test_student_create_view_get(self):
        """Test affichage du formulaire de création."""
        response = self.client.get(reverse('students:student_create'))
        self.assertEqual(response.status_code, 200)

    def test_student_create_view_post(self):
        """Test création d'un élève via le formulaire."""
        new_user = User.objects.create_user(
            email='newstudent@test.com', username='newstudent',
            role=Role.STUDENT, password='pass123',
            first_name='Nouveau', last_name='Élève'
        )
        response = self.client.post(reverse('students:student_create'), {
            'user': new_user.pk,
            'school': self.school.pk,
            'sexe': 'F',
            'lieu_naissance': 'Parakou',
            'nationalite': 'Béninoise',
        })
        self.assertRedirects(response, reverse('students:student_list'))
        self.assertTrue(Student.objects.filter(user=new_user).exists())

    def test_student_update_view(self):
        """Test modification d'un élève."""
        response = self.client.post(reverse('students:student_update', args=[self.student.pk]), {
            'user': self.student_user.pk,
            'school': self.school.pk,
            'sexe': 'F',
            'lieu_naissance': 'Cotonou',
            'nationalite': 'Béninoise',
        })
        self.assertRedirects(response, reverse('students:student_list'))
        self.student.refresh_from_db()
        self.assertEqual(self.student.sexe, 'F')

    def test_student_deactivate_view(self):
        """Test désactivation logique d'un élève."""
        response = self.client.post(reverse('students:student_deactivate', args=[self.student.pk]))
        self.assertRedirects(response, reverse('students:student_list'))
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_active)


# ============================================================================
# TESTS DE PERMISSIONS — apps/students
# ============================================================================

class StudentPermissionTestCase(TestCase):
    """Tests des contrôles d'accès par rôle sur les vues étudiants."""

    def setUp(self):
        self.school = School.objects.create(
            nom='Lycée Test', code='LYC01', adresse='123 Rue',
            telephone='+229 21 00 00 00', email='contact@lyceetest.bj',
            directeur_nom='M. Directeur'
        )
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
        )

    def test_admin_can_access_student_list(self):
        """ADMIN peut accéder à la liste."""
        admin = User.objects.create_user(
            email='admin@test.com', username='admin',
            role=Role.ADMIN, password='pass123'
        )
        self.client.force_login(admin)
        response = self.client.get(reverse('students:student_list'))
        self.assertEqual(response.status_code, 200)

    def test_director_can_access_student_list(self):
        """DIRECTOR peut accéder à la liste."""
        director = User.objects.create_user(
            email='director@test.com', username='director',
            role=Role.DIRECTOR, password='pass123'
        )
        self.client.force_login(director)
        response = self.client.get(reverse('students:student_list'))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_student_list(self):
        """Un élève ne peut pas accéder à la liste des élèves."""
        self.client.force_login(self.student_user)
        response = self.client.get(reverse('students:student_list'))
        self.assertEqual(response.status_code, 302)

    def test_teacher_cannot_access_student_list(self):
        """Un enseignant ne peut pas accéder à la liste des élèves."""
        teacher_user = User.objects.create_user(
            email='teacher@test.com', username='teacher',
            role=Role.TEACHER, password='pass123'
        )
        self.client.force_login(teacher_user)
        response = self.client.get(reverse('students:student_list'))
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_cannot_access_student_list(self):
        """Un utilisateur non connecté est redirigé vers le login."""
        response = self.client.get(reverse('students:student_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login').lstrip('/'), response.url)