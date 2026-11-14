from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from apps.accounts.models import Role


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Accès réservé à l'admin, au directeur et aux enseignants."""
    allowed_roles = {Role.ADMIN, Role.DIRECTOR, Role.TEACHER}

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.role in self.allowed_roles