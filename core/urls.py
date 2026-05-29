from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='clients/', permanent=False)),
    path('clients/', views.ClientListView.as_view()),
    path('ingest/', views.IngestView.as_view()),
    path('dashboard/', views.DashboardView.as_view()),
    path('records/<str:record_id>/review/', views.RecordReviewView.as_view()),
    path('batches/', views.BatchListView.as_view()),
    path('batches/<str:batch_id>/errors/', views.ParseErrorView.as_view()),
]