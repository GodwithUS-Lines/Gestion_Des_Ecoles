from django.test import TestCase
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.accounts.models import User, Role

User = get_user_model()


class UserModelTestCase(TestCase):
    """Tests pour le modèle User personnalisé."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            username='admin',
            password='admin123',
            role=Role.ADMIN
        )

    def test_create_user_with_email(self):
        """Test création utilisateur avec email comme identifiant."""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            role=Role.STUDENT,
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.role, Role.STUDENT)
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)

    def test_create_user_email_unique(self):
        """Test unicité de l'email (RG02 - matricule unique par établissement)."""
        User.objects.create_user(
            email='unique@test.com',
            username='user1',
            role=Role.STUDENT,
            password='pass123'
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='unique@test.com',  # même email
                username='user2',
                role=Role.STUDENT,
                password='pass123'
            )

    def test_create_superuser(self):
        """Test création superutilisateur (doit être ADMIN)."""
        superuser = User.objects.create_superuser(
            email='super@test.com',
            username='super',
            password='super123'
        )
        self.assertEqual(superuser.role, Role.ADMIN)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_superuser_must_be_admin(self):
        """Test qu'un superuser doit avoir le rôle ADMIN."""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='bad@test.com',
                username='bad',
                password='pass123',
                role=Role.TEACHER
            )

    def test_user_role_properties(self):
        """Test les propriétés de rôle (is_admin, is_teacher, etc.)."""
        teacher = User.objects.create_user(
            email='teacher@test.com',
            username='teacher',
            role=Role.TEACHER,
            password='pass123'
        )
        self.assertTrue(teacher.is_teacher)
        self.assertFalse(teacher.is_student)
        self.assertFalse(teacher.is_admin)

        student = User.objects.create_user(
            email='student@test.com',
            username='student',
            role=Role.STUDENT,
            password='pass123'
        )
        self.assertTrue(student.is_student)
        self.assertFalse(student.is_teacher)

        admin = User.objects.create_user(
            email='admin2@test.com',
            username='admin2',
            role=Role.ADMIN,
            password='pass123'
        )
        self.assertTrue(admin.is_admin)

    def test_user_str_representation(self):
        """Test la représentation string de l'utilisateur."""
        user = User.objects.create_user(
            email='test@test.com',
            username='test',
            role=Role.TEACHER,
            first_name='Jean',
            last_name='Dupont',
            password='pass123'
        )
        self.assertEqual(str(user), 'Jean Dupont (Enseignant)')

    def test_email_normalization(self):
        """Test normalisation de l'email (minuscules)."""
        user = User.objects.create_user(
            email='TEST@EXAMPLE.COM',
            username='testnorm',
            role=Role.STUDENT,
            password='pass123'
        )
        self.assertEqual(user.email, 'test@example.com')

    def test_get_dashboard_url_by_role(self):
        """Test redirection selon le rôle."""
        admin = User.objects.create_user(email='a@t.com', username='a', role=Role.ADMIN, password='p')
        teacher = User.objects.create_user(email='b@t.com', username='b', role=Role.TEACHER, password='p')
        student = User.objects.create_user(email='c@t.com', username='c', role=Role.STUDENT, password='p')

        self.assertEqual(admin.get_dashboard_url(), 'admin:index')
        self.assertEqual(teacher.get_dashboard_url(), 'dashboard')
        self.assertEqual(student.get_dashboard_url(), 'dashboard')


class AuthenticationBackendTestCase(TestCase):
    """Tests pour le backend d'authentification email/username."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='auth@test.com',
            username='authuser',
            role=Role.TEACHER,
            password='testpass123'
        )

    def test_authenticate_by_email(self):
        """Test authentification par email."""
        user = authenticate(username='auth@test.com', password='testpass123')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'authuser')

    def test_authenticate_by_username(self):
        """Test authentification par username."""
        user = authenticate(username='authuser', password='testpass123')
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'auth@test.com')

    def test_authenticate_case_insensitive_email(self):
        """Test authentification email insensible à la casse."""
        user = authenticate(username='AUTH@TEST.COM', password='testpass123')
        self.assertIsNotNone(user)

    def test_authenticate_wrong_password(self):
        """Test échec avec mauvais mot de passe."""
        user = authenticate(username='auth@test.com', password='wrongpass')
        self.assertIsNone(user)

    def test_authenticate_nonexistent_user(self):
        """Test échec avec utilisateur inexistant."""
        user = authenticate(username='nonexistent@test.com', password='pass123')
        self.assertIsNone(user)

    def test_authenticate_inactive_user(self):
        """Test échec avec utilisateur désactivé (RG19)."""
        self.user.is_active = False
        self.user.save()
        user = authenticate(username='auth@test.com', password='testpass123')
        self.assertIsNone(user)


class UserManagerTestCase(TestCase):
    """Tests pour le manager UserManager."""

    def test_create_user_requires_email(self):
        """Test que l'email est obligatoire."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', username='test', role=Role.STUDENT, password='pass123')

    def test_create_user_requires_username(self):
        """Test que le username est obligatoire."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='test@test.com', username='', role=Role.STUDENT, password='pass123')

    def test_create_user_requires_role(self):
        """Test que le rôle est obligatoire."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='test@test.com', username='test', role='', password='pass123')


class LogoutViewTestCase(TestCase):
    """Tests pour la vue de déconnexion (GET et POST)."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='logout@test.com',
            username='logoutuser',
            role=Role.STUDENT,
            password='testpass123'
        )
        self.logout_url = reverse('accounts:logout')
        self.login_url = reverse('accounts:login')

    def test_logout_get_redirects_to_login(self):
        """Test déconnexion via GET redirige vers login."""
        self.client.force_login(self.user)
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.login_url)
        # Vérifier que l'utilisateur est déconnecté
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_post_redirects_to_login(self):
        """Test déconnexion via POST redirige vers login."""
        self.client.force_login(self.user)
        response = self.client.post(self.logout_url)
        self.assertRedirects(response, self.login_url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_get_shows_message(self):
        """Test message de déconnexion affiché."""
        self.client.force_login(self.user)
        response = self.client.get(self.logout_url, follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any('déconnecté' in str(m).lower() for m in messages))

    def test_logout_anonymous_user(self):
        """Test déconnexion utilisateur anonyme (ne doit pas planter)."""
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.login_url)