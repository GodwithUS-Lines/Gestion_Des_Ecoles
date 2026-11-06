from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Parent URLs
    path('parents/', views.ParentListView.as_view(), name='parent_list'),
    path('parents/creer/', views.ParentCreateView.as_view(), name='parent_create'),
    path('parents/<int:pk>/', views.ParentDetailView.as_view(), name='parent_detail'),
    path('parents/<int:pk>/modifier/', views.ParentUpdateView.as_view(), name='parent_update'),
    path('parents/<int:pk>/desactiver/', views.ParentDeactivateView.as_view(), name='parent_deactivate'),

    # Student URLs
    path('', views.StudentListView.as_view(), name='student_list'),
    path('creer/', views.StudentCreateView.as_view(), name='student_create'),
    path('<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('<int:pk>/modifier/', views.StudentUpdateView.as_view(), name='student_update'),
    path('<int:pk>/desactiver/', views.StudentDeactivateView.as_view(), name='student_deactivate'),
]