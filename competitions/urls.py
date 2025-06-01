from django.urls import path
from . import views

app_name = 'competitions'  # This is the important line to add

urlpatterns = [
    # Your URL patterns here
    # For example:
    # path('', views.CompetitionListView.as_view(), name='competition-list'),
    # path('create/', views.CompetitionCreateView.as_view(), name='competition-create'),
    # path('<int:pk>/', views.CompetitionDetailView.as_view(), name='competition-detail'),
]