from rest_framework import viewsets
from .models import MemberRegistration
from .serializers import MemberRegistrationSerializer

class MemberRegistrationViewSet(viewsets.ModelViewSet):
    queryset = MemberRegistration.objects.all()
    serializer_class = MemberRegistrationSerializer
