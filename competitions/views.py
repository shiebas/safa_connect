from django.shortcuts import render
from rest_framework import viewsets
from .models import Competition
from .serializers import CompetitionSerializer

# Create your views here.

class CompetitionViewSet(viewsets.ModelViewSet):
    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer
