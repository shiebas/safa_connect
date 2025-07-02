from django.urls import path
from . import views

app_name = 'legal'

urlpatterns = [
    path('terms/', views.terms_and_conditions, name='terms'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('cookies/', views.cookie_policy, name='cookies'),
    path('paia/', views.paia_act, name='paia'),
    path('refund/', views.refund_policy, name='refund'),
]
