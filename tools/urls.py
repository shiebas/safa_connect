from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    path('generate-all-safa-ids/', views.generate_all_safa_ids, name='generate_all_safa_ids'),
    path('safa-id-coverage/', views.safa_id_coverage, name='safa_id_coverage'),
]
