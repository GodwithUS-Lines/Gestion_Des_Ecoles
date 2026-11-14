from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.AttendanceListView.as_view(), name="list"),
    path("ajouter/", views.AttendanceCreateView.as_view(), name="create"),
    path("<int:pk>/modifier/", views.AttendanceUpdateView.as_view(), name="update"),
    path("<int:pk>/supprimer/", views.AttendanceDeleteView.as_view(), name="delete"),
]