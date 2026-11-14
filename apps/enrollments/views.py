from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View

from apps.accounts.models import Role
from .models import Enrollment
from .forms import EnrollmentForm, EnrollmentSearchForm


class AdminOrDirectorRequiredMixin(UserPassesTestMixin):
    """Mixin pour restreindre l'accès aux admins et directeurs."""

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role in {Role.ADMIN, Role.DIRECTOR}

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('accounts:login')
        messages.error(self.request, _('Accès non autorisé. Seuls les administrateurs et directeurs peuvent accéder à ce module.'))
        return redirect('dashboard')


class EnrollmentListView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, ListView):
    """Liste des inscriptions avec recherche et filtres."""

    model = Enrollment
    template_name = 'enrollments/enrollment_list.html'
    context_object_name = 'enrollments'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'student', 'student__user', 'classroom', 'academic_year'
        )

        # Recherche
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(student__user__first_name__icontains=search) |
                Q(student__user__last_name__icontains=search) |
                Q(student__matricule__icontains=search) |
                Q(numero_inscription__icontains=search) |
                Q(classroom__nom__icontains=search)
            )

        # Filtres
        academic_year_id = self.request.GET.get('academic_year')
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)

        classroom_id = self.request.GET.get('classroom')
        if classroom_id:
            queryset = queryset.filter(classroom_id=classroom_id)

        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = EnrollmentSearchForm(self.request.GET)
        return context


class EnrollmentDetailView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, DetailView):
    """Détail d'une inscription."""

    model = Enrollment
    template_name = 'enrollments/enrollment_detail.html'
    context_object_name = 'enrollment'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'student', 'student__user', 'classroom', 'academic_year'
        )


class EnrollmentCreateView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, CreateView):
    """Création d'une inscription."""

    model = Enrollment
    form_class = EnrollmentForm
    template_name = 'enrollments/enrollment_form.html'
    success_url = reverse_lazy('enrollments:enrollment_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Filtrer par l'école de l'utilisateur si applicable
        # Pour l'instant, on passe l'école de l'utilisateur connecté si applicable
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('Inscription créée avec succès.'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nouvelle inscription')
        context['submit_text'] = _('Inscrire')
        return context


class EnrollmentUpdateView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, UpdateView):
    """Modification d'une inscription."""

    model = Enrollment
    form_class = EnrollmentForm
    template_name = 'enrollments/enrollment_form.html'
    success_url = reverse_lazy('enrollments:enrollment_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('Inscription modifiée avec succès.'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Modifier l\'inscription')
        context['submit_text'] = _('Enregistrer')
        return context


class EnrollmentCancelView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, View):
    """Annulation d'une inscription (statut ANNULEE)."""

    template_name = 'enrollments/enrollment_confirm_cancel.html'
    success_url = reverse_lazy('enrollments:enrollment_list')

    def get(self, request, *args, **kwargs):
        enrollment = get_object_or_404(Enrollment, pk=kwargs['pk'])
        return render(request, self.template_name, {
            'enrollment': enrollment,
            'title': _('Annuler l\'inscription'),
        })

    def post(self, request, *args, **kwargs):
        enrollment = get_object_or_404(Enrollment, pk=kwargs['pk'])
        if enrollment.statut == Enrollment.Statut.ANNULEE or not enrollment.is_active:
            messages.info(request, _('Cette inscription est déjà annulée.'))
        else:
            enrollment.annuler()
            messages.success(request, _('Inscription annulée avec succès.'))
        return redirect(self.success_url)


class EnrollmentTerminateView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, View):
    """Terminer une inscription (statut TERMINEE)."""

    template_name = 'enrollments/enrollment_confirm_terminate.html'
    success_url = reverse_lazy('enrollments:enrollment_list')

    def get(self, request, *args, **kwargs):
        enrollment = get_object_or_404(Enrollment, pk=kwargs['pk'])
        return render(request, self.template_name, {
            'enrollment': enrollment,
            'title': _('Terminer l\'inscription'),
        })

    def post(self, request, *args, **kwargs):
        enrollment = get_object_or_404(Enrollment, pk=kwargs['pk'])
        if enrollment.statut == Enrollment.Statut.TERMINEE:
            messages.info(request, _('Cette inscription est déjà terminée.'))
        else:
            enrollment.terminer()
            messages.success(request, _('Inscription terminée avec succès.'))
        return redirect(self.success_url)


class EnrollmentSuspendView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, View):
    """Suspendre une inscription (statut SUSPENDUE)."""

    template_name = 'enrollments/enrollment_confirm_suspend.html'
    success_url = reverse_lazy('enrollments:enrollment_list')

    def get(self, request, *args, **kwargs):
        enrollment = get_object_or_404(Enrollment, pk=kwargs['pk'])
        return render(request, self.template_name, {
            'enrollment': enrollment,
            'title': _('Suspendre l\'inscription'),
        })

    def post(self, request, *args, **kwargs):
        enrollment = get_object_or_404(Enrollment, pk=kwargs['pk'])
        if enrollment.statut == Enrollment.Statut.SUSPENDUE:
            messages.info(request, _('Cette inscription est déjà suspendue.'))
        else:
            enrollment.suspendre()
            messages.success(request, _('Inscription suspendue avec succès.'))
        return redirect(self.success_url)


class EnrollmentReactivateView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, View):
    """Réactiver une inscription suspendue (statut ACTIVE)."""

    template_name = 'enrollments/enrollment_confirm_reactivate.html'
    success_url = reverse_lazy('enrollments:enrollment_list')

    def get(self, request, *args, **kwargs):
        enrollment = get_object_or_404(Enrollment, pk=kwargs['pk'])
        return render(request, self.template_name, {
            'enrollment': enrollment,
            'title': _('Réactiver l\'inscription'),
        })

    def post(self, request, *args, **kwargs):
        enrollment = get_object_or_404(Enrollment, pk=kwargs['pk'])
        if enrollment.statut != Enrollment.Statut.SUSPENDUE:
            messages.info(request, _('Une inscription ne peut être réactivée que si elle est suspendue.'))
        else:
            enrollment.reactiver()
            messages.success(request, _('Inscription réactivée avec succès.'))
        return redirect(self.success_url)