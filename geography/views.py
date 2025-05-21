from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import (
    Country, Province, Region, WorldSportsBody, Continent,
    ContinentFederation, Club, Association, Membership
)
from django.shortcuts import render
import datetime
from django.views.generic import CreateView

# Advanced global home page
def advanced_home(request):
    countries = Country.objects.all().order_by('name')
    return render(request, "home.html", {
        "countries": countries,
        "year": datetime.datetime.now().year,
    })

# Admin dashboard view for the geography app
@login_required
def geography_admin(request):
    return render(request, "geography/geography_admin.html")

# Decorator for all CBVs
login_decorator = method_decorator(login_required, name='dispatch')

# --- Country ---
@login_decorator
class CountryListView(ListView):
    model = Country
    template_name = 'geography/country_list.html'
    context_object_name = 'countries'

@login_decorator
class CountryDetailView(DetailView):
    model = Country
    template_name = 'geography/country_detail.html'
    context_object_name = 'country'

# --- Province ---
@login_decorator
class ProvinceListView(ListView):
    model = Province
    template_name = 'geography/province_list.html'
    context_object_name = 'provinces'

@login_decorator
class ProvinceDetailView(DetailView):
    model = Province
    template_name = 'geography/province_detail.html'
    context_object_name = 'province'

# --- Region ---
@login_decorator
class RegionListView(ListView):
    model = Region
    template_name = 'geography/region_list.html'
    context_object_name = 'regions'

@login_decorator
class RegionDetailView(DetailView):
    model = Region
    template_name = 'geography/region_detail.html'
    context_object_name = 'region'

# --- WorldSportsBody ---
@login_decorator
class WorldSportsBodyListView(ListView):
    model = WorldSportsBody
    template_name = 'geography/worldsportsbody_list.html'
    context_object_name = 'worldsportsbodies'

@login_decorator
class WorldSportsBodyDetailView(DetailView):
    model = WorldSportsBody
    template_name = 'geography/worldsportsbody_detail.html'
    context_object_name = 'worldsportsbody'

@login_decorator
class WorldSportsBodyCreateView(CreateView):
    model = WorldSportsBody
    template_name = 'geography/worldsportsbody_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:worldsportsbody-list')

# --- Continent ---
@login_decorator
class ContinentListView(ListView):
    model = Continent
    template_name = 'geography/continent_list.html'
    context_object_name = 'continents'

@login_decorator
class ContinentDetailView(DetailView):
    model = Continent
    template_name = 'geography/continent_detail.html'
    context_object_name = 'continent'

# --- ContinentFederation ---
@login_decorator
class ContinentFederationListView(ListView):
    model = ContinentFederation
    template_name = 'geography/continentfederation_list.html'
    context_object_name = 'continentfederations'

@login_decorator
class ContinentFederationDetailView(DetailView):
    model = ContinentFederation
    template_name = 'geography/continentfederation_detail.html'
    context_object_name = 'continentfederation'

# --- Club ---
@login_decorator
class ClubListView(ListView):
    model = Club
    template_name = 'geography/club_list.html'
    context_object_name = 'clubs'

@login_decorator
class ClubDetailView(DetailView):
    model = Club
    template_name = 'geography/club_detail.html'
    context_object_name = 'club'

# --- Association ---
@login_decorator
class AssociationListView(ListView):
    model = Association
    template_name = 'geography/association_list.html'
    context_object_name = 'associations'

@login_decorator
class AssociationDetailView(DetailView):
    model = Association
    template_name = 'geography/association_detail.html'
    context_object_name = 'association'

# --- Membership ---
@login_decorator
class MembershipListView(ListView):
    model = Membership
    template_name = 'geography/membership_list.html'
    context_object_name = 'memberships'

@login_decorator
class MembershipDetailView(DetailView):
    model = Membership
    template_name = 'geography/membership_detail.html'
    context_object_name = 'membership'