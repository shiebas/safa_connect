from django.urls import path
from . import views

app_name = 'pdf_processor'

urlpatterns = [
    # PDF Upload
    path('upload/', views.PDFUploadView.as_view(), name='pdf-upload'),
    path('upload/success/', views.pdf_upload_success, name='pdf-upload-success'),
    
    # PDF List and Detail
    path('', views.PDFListView.as_view(), name='pdf-list'),
    path('<int:pk>/', views.PDFDetailView.as_view(), name='pdf-detail'),
    
    # PDF Processing
    path('<int:pk>/process/', views.PDFProcessView.as_view(), name='pdf-process'),
    
    # PDF Data Export
    path('<int:pk>/export/', views.PDFDataExportView.as_view(), name='pdf-export'),
]