from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from apps.accounts.models import Role
from .models import Parent, Student
from .forms import ParentForm, StudentForm, StudentSearchForm


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


class StudentListView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, ListView):
    """Liste des élèves avec recherche et filtres."""

    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user', 'school', 'parent', 'parent__user')

        # Recherche
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(matricule__icontains=search) |
                Q(lieu_naissance__icontains=search)
            )

        # Filtre école
        school_id = self.request.GET.get('school')
        if school_id:
            queryset = queryset.filter(school_id=school_id)

        # Filtre statut
        is_active = self.request.GET.get('is_active')
        if is_active == 'True':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'False':
            queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = StudentSearchForm(self.request.GET)
        return context


class StudentDetailView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, DetailView):
    """Détail d'un élève."""

    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'user', 'school', 'parent', 'parent__user'
        ).prefetch_related('enrollments__classroom', 'enrollments__academic_year')


class StudentCreateView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, CreateView):
    """Création d'un élève."""

    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:student_list')

    def form_valid(self, form):
        messages.success(self.request, _('Élève créé avec succès.'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nouvel élève')
        context['submit_text'] = _('Créer')
        return context


class StudentUpdateView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, UpdateView):
    """Modification d'un élève."""

    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:student_list')

    def form_valid(self, form):
        messages.success(self.request, _('Élève modifié avec succès.'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Modifier l\'élève')
        context['submit_text'] = _('Enregistrer')
        return context


class StudentDeactivateView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, DeleteView):
    """Désactivation d'un élève (RG19 - soft delete)."""

    model = Student
    template_name = 'students/student_confirm_deactivate.html'
    success_url = reverse_lazy('students:student_list')
    context_object_name = 'student'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.is_active:
            messages.info(request, _('Cet élève est déjà désactivé.'))
            return redirect(self.success_url)
        self.object.is_active = False
        self.object.save(update_fields=['is_active', 'date_modification'])
        messages.success(request, _('Élève désactivé avec succès.'))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Désactiver l\'élève')
        return context


class ParentListView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, ListView):
    """Liste des parents."""

    model = Parent
    template_name = 'students/parent_list.html'
    context_object_name = 'parents'
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().select_related('user')


class ParentDetailView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, DetailView):
    """Détail d'un parent."""

    model = Parent
    template_name = 'students/parent_detail.html'
    context_object_name = 'parent'

    def get_queryset(self):
        return super().get_queryset().select_related('user').prefetch_related('enfants__user')


class ParentCreateView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, CreateView):
    """Création d'un parent."""

    model = Parent
    form_class = ParentForm
    template_name = 'students/parent_form.html'
    success_url = reverse_lazy('students:parent_list')

    def form_valid(self, form):
        messages.success(self.request, _('Parent créé avec succès.'))
        return super().form_valid(form)


class ParentUpdateView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, UpdateView):
    """Modification d'un parent."""

    model = Parent
    form_class = ParentForm
    template_name = 'students/parent_form.html'
    success_url = reverse_lazy('students:parent_list')

    def form_valid(self, form):
        messages.success(self.request, _('Parent modifié avec succès.'))
        return super().form_valid(form)


class ParentDeactivateView(LoginRequiredMixin, AdminOrDirectorRequiredMixin, DeleteView):
    """Désactivation d'un parent (RG19 - soft delete)."""

    model = Parent
    template_name = 'students/parent_confirm_deactivate.html'
    success_url = reverse_lazy('students:parent_list')
    context_object_name = 'parent'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.is_active:
            messages.info(request, _('Ce parent est déjà désactivé.'))
            return redirect(self.success_url)
        self.object.is_active = False
        self.object.save(update_fields=['is_active', 'date_modification'])
        messages.success(request, _('Parent désactivé avec succès.'))
        return redirect(self.success_url)