from django.urls import path
from . import views

app_name = 'enrollments'

urlpatterns = [
    path('', views.EnrollmentListView.as_view(), name='enrollment_list'),
    path('creer/', views.EnrollmentCreateView.as_view(), name='enrollment_create'),
    path('<int:pk>/', views.EnrollmentDetailView.as_view(), name='enrollment_detail'),
    path('<int:pk>/modifier/', views.EnrollmentUpdateView.as_view(), name='enrollment_update'),
    path('<int:pk>/annuler/', views.EnrollmentCancelView.as_view(), name='enrollment_cancel'),
    path('<int:pk>/terminer/', views.EnrollmentTerminateView.as_view(), name='enrollment_terminate'),
    path('<int:pk>/suspendre/', views.EnrollmentSuspendView.as_view(), name='enrollment_suspend'),
    path('<int:pk>/reactiver/', views.EnrollmentReactivateView.as_view(), name='enrollment_reactivate'),
]