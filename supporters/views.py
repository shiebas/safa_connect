from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import SupporterRegistrationForm
from .models import SupporterProfile
from accounts.models import CustomUser
from rest_framework import viewsets
from .serializers import SupporterProfileSerializer
from .permissions import IsSupporterSelfOrReadOnly

@login_required
def register_supporter(request):
    user = request.user
    try:
        profile = user.supporterprofile
        return redirect('supporters:profile')
    except SupporterProfile.DoesNotExist:
        pass
    if request.method == 'POST':
        form = SupporterRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            supporter = form.save(commit=False)
            supporter.user = user
            supporter.save()
            return redirect('supporters:profile')
    else:
        form = SupporterRegistrationForm()
    return render(request, 'supporters/register.html', {'form': form})

@login_required
def supporter_profile(request):
    profile = request.user.supporterprofile
    return render(request, 'supporters/profile.html', {'profile': profile})

class SupporterProfileViewSet(viewsets.ModelViewSet):
    queryset = SupporterProfile.objects.all()
    serializer_class = SupporterProfileSerializer
    permission_classes = [IsSupporterSelfOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'supporterprofile'):
            return SupporterProfile.objects.filter(user=user)
        return super().get_queryset()
