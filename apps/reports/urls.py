from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportCardListView.as_view(), name="list"),
    path("generer/", views.GenerateReportCardsView.as_view(), name="generate"),
    path("<int:pk>/", views.ReportCardDetailView.as_view(), name="detail"),
]