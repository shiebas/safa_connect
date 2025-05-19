# geography/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import (
    WorldSportsBody, 
    Continent, 
    ContinentFederation,
    ContinentRegion,
    Country,
    NationalFederation,
    Province,
    Region,
    Association,
    Club,
    CustomUser,
    Membership
)
from .forms import (
    RegistrationForm,
    LoginForm,
    ProfileForm,
    MembershipForm
)

# Basic views
def home(request):
    """Home page with overview of the sports system"""
    # Count statistics for dashboard
    stats = {
        'world_bodies': WorldSportsBody.objects.count(),
        'countries': Country.objects.count(),
        'federations': NationalFederation.objects.count(),
        'clubs': Club.objects.count(),
        'members': CustomUser.objects.count()
    }
    
    # Featured items
    featured_sport = WorldSportsBody.objects.filter(sport_code='SOCCER').first()
    featured_federation = None
    featured_clubs = None
    
    # If user is logged in, get context relevant to their country
    if request.user.is_authenticated and request.user.country:
        user_country = request.user.country
        featured_federation = NationalFederation.objects.filter(country=user_country).first()
        featured_clubs = Club.objects.filter(
            region__province__country=user_country
        ).order_by('?')[:5]  # Random 5 clubs
    
    context = {
        'stats': stats,
        'featured_sport': featured_sport,
        'featured_federation': featured_federation,
        'featured_clubs': featured_clubs
    }
    return render(request, 'geography/home.html', context)

# World Sports Bodies views
def world_bodies_list(request):
    """List all world sports bodies"""
    bodies = WorldSportsBody.objects.all().order_by('name')
    return render(request, 'geography/world_bodies_list.html', {'bodies': bodies})

def world_body_detail(request, pk):
    """Detail view for a specific world sports body"""
    body = get_object_or_404(WorldSportsBody, pk=pk)
    federations = body.continent_federations.all()
    context = {
        'body': body,
        'federations': federations
    }
    return render(request, 'geography/world_body_detail.html', context)

# Continent views
def continent_list(request):
    """List all continents"""
    continents = Continent.objects.all().order_by('name')
    return render(request, 'geography/continent_list.html', {'continents': continents})

def continent_detail(request, pk):
    """Detail view for a specific continent"""
    continent = get_object_or_404(Continent, pk=pk)
    federations = continent.federations.all()
    context = {
        'continent': continent,
        'federations': federations
    }
    return render(request, 'geography/continent_detail.html', context)

# Continental Federation views
def continent_federation_list(request):
    """List all continental federations"""
    federations = ContinentFederation.objects.all().order_by('name')
    return render(request, 'geography/continent_federation_list.html', {'federations': federations})

def continent_federation_detail(request, pk):
    """Detail view for a specific continental federation"""
    federation = get_object_or_404(ContinentFederation, pk=pk)
    regions = federation.regions.all()
    context = {
        'federation': federation,
        'regions': regions
    }
    return render(request, 'geography/continent_federation_detail.html', context)

# Continental Region views
def continent_region_list(request):
    """List all continental regions"""
    regions = ContinentRegion.objects.all().order_by('name')
    return render(request, 'geography/continent_region_list.html', {'regions': regions})

def continent_region_detail(request, pk):
    """Detail view for a specific continental region"""
    region = get_object_or_404(ContinentRegion, pk=pk)
    countries = region.countries.all()
    context = {
        'region': region,
        'countries': countries
    }
    return render(request, 'geography/continent_region_detail.html', context)

# Country views
def country_list(request):
    """List all countries"""
    countries = Country.objects.all().order_by('name')
    return render(request, 'geography/country_list.html', {'countries': countries})

def country_detail(request, pk):
    """Detail view for a specific country"""
    country = get_object_or_404(Country, pk=pk)
    federations = country.federations.all()
    provinces = country.provinces.all()
    context = {
        'country': country,
        'federations': federations,
        'provinces': provinces
    }
    return render(request, 'geography/country_detail.html', context)

# National Federation views
def national_federation_list(request):
    """List all national federations"""
    federations = NationalFederation.objects.all().order_by('name')
    return render(request, 'geography/national_federation_list.html', {'federations': federations})

def national_federation_detail(request, pk):
    """Detail view for a specific national federation"""
    federation = get_object_or_404(NationalFederation, pk=pk)
    regions = federation.regions.all()
    associations = federation.associations.all()
    context = {
        'federation': federation,
        'regions': regions,
        'associations': associations
    }
    return render(request, 'geography/national_federation_detail.html', context)

# Province views
def province_list(request):
    """List all provinces"""
    provinces = Province.objects.all().order_by('name')
    return render(request, 'geography/province_list.html', {'provinces': provinces})

def province_detail(request, pk):
    """Detail view for a specific province"""
    province = get_object_or_404(Province, pk=pk)
    regions = province.regions.all()
    context = {
        'province': province,
        'regions': regions
    }
    return render(request, 'geography/province_detail.html', context)

# Region views
def region_list(request):
    """List all regions"""
    regions = Region.objects.all().order_by('name')
    return render(request, 'geography/region_list.html', {'regions': regions})

def region_detail(request, pk):
    """Detail view for a specific region"""
    region = get_object_or_404(Region, pk=pk)
    clubs = region.clubs.all()
    context = {
        'region': region,
        'clubs': clubs
    }
    return render(request, 'geography/region_detail.html', context)

# Club views
def club_list(request):
    """List all clubs"""
    clubs = Club.objects.all().order_by('name')
    return render(request, 'geography/club_list.html', {'clubs': clubs})

def club_detail(request, pk):
    """Detail view for a specific club"""
    club = get_object_or_404(Club, pk=pk)
    # Get active members of this club
    members = Membership.objects.filter(club=club, is_active=True).select_related('user')
    context = {
        'club': club,
        'members': members
    }
    return render(request, 'geography/club_detail.html', context)

# Association views
def association_list(request):
    """List all associations"""
    associations = Association.objects.all().order_by('name')
    return render(request, 'geography/association_list.html', {'associations': associations})

def association_detail(request, pk):
    """Detail view for a specific association"""
    association = get_object_or_404(Association, pk=pk)
    members = Membership.objects.filter(association=association, is_active=True).select_related('user')
    context = {
        'association': association,
        'members': members
    }
    return render(request, 'geography/association_detail.html', context)

# User authentication and registration views
def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to the Global Sports System.")
            return redirect('geography:profile')
    else:
        form = RegistrationForm()
    
    return render(request, 'geography/register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Login successful!")
                return redirect('geography:profile')
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    
    return render(request, 'geography/login.html', {'form': form})

def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('geography:home')

# User profile views
@login_required
def profile(request):
    """User profile view"""
    user = request.user
    memberships = Membership.objects.filter(user=user)
    
    context = {
        'user': user,
        'memberships': memberships
    }
    return render(request, 'geography/profile.html', context)

@login_required
def edit_profile(request):
    """Edit user profile view"""
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated!")
            return redirect('geography:profile')
    else:
        form = ProfileForm(instance=request.user)
    
    return render(request, 'geography/edit_profile.html', {'form': form})

# Membership views
@login_required
def memberships(request):
    """View user's memberships"""
    memberships = Membership.objects.filter(user=request.user)
    return render(request, 'geography/memberships.html', {'memberships': memberships})

@login_required
def new_membership(request):
    """Create new membership"""
    if request.method == 'POST':
        form = MembershipForm(request.POST)
        if form.is_valid():
            membership = form.save(commit=False)
            membership.user = request.user
            membership.save()
            messages.success(request, "Your membership has been created!")
            return redirect('geography:memberships')
    else:
        form = MembershipForm()
    
    return render(request, 'geography/membership_form.html', {'form': form, 'is_new': True})

@login_required
def edit_membership(request, pk):
    """Edit existing membership"""
    membership = get_object_or_404(Membership, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = MembershipForm(request.POST, instance=membership)
        if form.is_valid():
            form.save()
            messages.success(request, "Your membership has been updated!")
            return redirect('geography:memberships')
    else:
        form = MembershipForm(instance=membership)
    
    return render(request, 'geography/membership_form.html', {'form': form, 'is_new': False})

# API views for dynamic form filtering
def regions_by_province(request, province_id):
    """AJAX view to get regions for a specific province"""
    regions = Region.objects.filter(province_id=province_id).values('id', 'name')
    return JsonResponse(list(regions), safe=False)

def clubs_by_region(request, region_id):
    """AJAX view to get clubs for a specific region"""
    clubs = Club.objects.filter(region_id=region_id).values('id', 'name')
    return JsonResponse(list(clubs), safe=False)
