from django.urls import path
from . import views

app_name = 'parking'

urlpatterns = [
    path('api/parking-data/', views.parking_data_api, name='parking_data_api'),
    path('allocation/<uuid:allocation_id>/', views.parking_allocation_detail, name='parking_allocation_detail'),
    path('allocate/<uuid:match_id>/', views.allocate_parking, name='allocate_parking'),
]
