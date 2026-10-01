from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _

from .forms import (
    CustomAuthenticationForm, CustomPasswordChangeForm,
    CustomPasswordResetForm, CustomSetPasswordForm,
    UserProfileForm
)


class CustomLoginView(LoginView):
    """Vue de connexion personnalisée."""
    form_class = CustomAuthenticationForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        """Redirection selon le rôle de l'utilisateur."""
        user = self.request.user
        if user.is_admin:
            return reverse_lazy('admin:index')
        return reverse_lazy('dashboard')

    def form_valid(self, form):
        """Connexion et message de bienvenue."""
        response = super().form_valid(form)
        user = self.request.user
        if not user.is_admin:
            from django.contrib import messages
            messages.success(self.request, _('Bienvenue, %(name)s !') % {'name': user.get_full_name() or user.username})
        return response


class CustomLogoutView(LogoutView):
    """Vue de déconnexion (accepte GET et POST pour compatibilité liens)."""
    next_page = reverse_lazy('accounts:login')
    http_method_names = ['get', 'post', 'options']

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            from django.contrib import messages
            messages.info(request, _('Vous avez été déconnecté.'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Permet la déconnexion via GET (lien direct)."""
        return self.post(request, *args, **kwargs)


class CustomPasswordChangeView(PasswordChangeView):
    """Changement de mot de passe."""
    form_class = CustomPasswordChangeForm
    template_name = 'registration/password_change.html'
    success_url = reverse_lazy('accounts:password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, form.user)
        return response


class CustomPasswordResetView(PasswordResetView):
    """Demande de réinitialisation."""
    form_class = CustomPasswordResetForm
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Confirmation d'envoi d'email."""
    template_name = 'registration/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Confirmation et définition du nouveau mot de passe."""
    form_class = CustomSetPasswordForm
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Réinitialisation terminée."""
    template_name = 'registration/password_reset_complete.html'


@login_required
def profile_view(request):
    """Profil utilisateur (lecture + modification)."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            from django.contrib import messages
            messages.success(request, _('Profil mis à jour avec succès.'))
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'user': request.user,
    })


class ProfileView(TemplateView):
    """Vue de profil en lecture seule (pour compatibilité)."""
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context