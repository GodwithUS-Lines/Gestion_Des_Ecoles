from django.urls import path
from . import views

app_name = "grades"

urlpatterns = [
    path("", views.GradeListView.as_view(), name="list"),
    path("ajouter/", views.GradeCreateView.as_view(), name="create"),
    path("<int:pk>/modifier/", views.GradeUpdateView.as_view(), name="update"),
    path("<int:pk>/supprimer/", views.GradeDeleteView.as_view(), name="delete"),
]