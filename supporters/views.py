from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import SupporterRegistrationForm
from .models import SupporterProfile
from accounts.models import CustomUser

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
