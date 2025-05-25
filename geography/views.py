from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import (
    Country, Province, Region, WorldSportsBody, Continent,
    ContinentFederation, Club, Association, Membership, ContinentRegion, NationalFederation
)

import datetime
from geography.forms import WorldSportsBodyForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render

# geography/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import ContinentFederationForm

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

# WorldSportsBody

class WorldSportsBodyListView(LoginRequiredMixin, ListView):
    model = WorldSportsBody
    template_name = 'geography/worldsportsbody_list.html'
    context_object_name = 'object_list'  # Use 'object_list' in your template

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(sport_code__icontains=q)
        return queryset

class WorldSportsBodyDetailView(LoginRequiredMixin, DetailView):
    model = WorldSportsBody
    template_name = 'geography/worldsportsbody_detail.html'
    context_object_name = 'object'

class WorldSportsBodyCreateView(LoginRequiredMixin, CreateView):
    model = WorldSportsBody
    form_class = WorldSportsBodyForm
    template_name = 'geography/worldsportsbody_form.html'
    success_url = reverse_lazy('geography:worldsportsbody-list')

class WorldSportsBodyUpdateView(LoginRequiredMixin, UpdateView):
    model = WorldSportsBody
    form_class = WorldSportsBodyForm
    template_name = 'geography/worldsportsbody_form.html'
    success_url = reverse_lazy('geography:worldsportsbody-list')

class WorldSportsBodyDeleteView(LoginRequiredMixin, DeleteView):
    model = WorldSportsBody
    template_name = 'geography/worldsportsbody_confirm_delete.html'
    success_url = reverse_lazy('geography:worldsportsbody-list')

# Continent
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

@login_decorator
class ContinentCreateView(CreateView):
    model = Continent
    template_name = 'geography/continent_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:continent-list')

@login_decorator
class ContinentUpdateView(UpdateView):
    model = Continent
    template_name = 'geography/continent_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:continent-list')

@login_decorator
class ContinentDeleteView(DeleteView):
    model = Continent
    template_name = 'geography/continent_confirm_delete.html'
    success_url = reverse_lazy('geography:continent-list') 

    
def get_worldsportsbodies_by_sport(request):
    sport_code = request.GET.get('sport_code')
    wsbs = WorldSportsBody.objects.filter(sport_code=sport_code).order_by('name')
    result = [{'id': wsb.id, 'name': wsb.name} for wsb in wsbs]
    return JsonResponse({'wsbs': result})


# ContinentFederation
@login_decorator
class ContinentFederationListView(ListView):
    model = ContinentFederation
    template_name = 'geography/continentfederation_list.html'
    context_object_name = 'federations'
    paginate_by = 20
    
    def get_queryset(self):
        return ContinentFederation.objects.select_related(
            'world_body', 'continent'
        ).order_by('sport_code', 'continent__name')




@login_decorator
class ContinentFederationDetailView(DetailView):
    model = ContinentFederation
    template_name = 'geography/continentfederation_detail.html'
    context_object_name = 'continentfederation'

@login_decorator
class ContinentFederationCreateView(CreateView):
    model = ContinentFederation
    form_class = ContinentFederationForm
    template_name = 'geography/continentfederation_form.html'
    success_url = reverse_lazy('geography:continentfederation_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Continent Federation created successfully!')
        return super().form_valid(form)

@login_decorator
class ContinentFederationUpdateView(UpdateView):
    model = ContinentFederation
    form_class = ContinentFederationForm
    template_name = 'geography/continentfederation_form.html'
    success_url = reverse_lazy('geography:continentfederation_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Continent Federation updated successfully!')
        return super().form_valid(form)

# Ajax Views
def ajax_get_worldsportsbodies(request):
    """Ajax view to get world sports bodies based on sport code"""
    sport_code = request.GET.get('sport_code')
    wsbs = []
    
    if sport_code:
        world_bodies = WorldSportsBody.objects.filter(sport_code=sport_code).order_by('name')
        wsbs = [{'id': wb.id, 'name': wb.name, 'acronym': wb.acronym} for wb in world_bodies]
    
    return JsonResponse({'wsbs': wsbs})

def ajax_get_continents(request):
    """Ajax view to get continents based on world sports body"""
    world_body_id = request.GET.get('world_body_id')
    continents = []
    
    if world_body_id:
        try:
            world_body = WorldSportsBody.objects.get(id=world_body_id)
            continents_qs = world_body.continents.all().order_by('name')
            continents = [{'id': c.id, 'name': c.name, 'code': c.code} for c in continents_qs]
        except WorldSportsBody.DoesNotExist:
            pass
    
    return JsonResponse({'continents': continents})

        

@login_decorator
class ContinentFederationDeleteView(DeleteView):
    model = ContinentFederation
    template_name = 'geography/continentfederation_confirm_delete.html'
    success_url = reverse_lazy('geography:continentfederation-list')

# ContinentRegion
@login_decorator
class ContinentRegionListView(ListView):
    model = ContinentRegion
    template_name = 'geography/continentregion_list.html'
    context_object_name = 'continentregions'

@login_decorator
class ContinentRegionDetailView(DetailView):
    model = ContinentRegion
    template_name = 'geography/continentregion_detail.html'
    context_object_name = 'continentregion'

@login_decorator
class ContinentRegionCreateView(CreateView):
    model = ContinentRegion
    template_name = 'geography/continentregion_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:continentregion-list')

@login_decorator
class ContinentRegionUpdateView(UpdateView):
    model = ContinentRegion
    template_name = 'geography/continentregion_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:continentregion-list')

@login_decorator
class ContinentRegionDeleteView(DeleteView):
    model = ContinentRegion
    template_name = 'geography/continentregion_confirm_delete.html'
    success_url = reverse_lazy('geography:continentregion-list')

# Country
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

@login_decorator
class CountryCreateView(CreateView):
    model = Country
    template_name = 'geography/country_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:country-list')

@login_decorator
class CountryUpdateView(UpdateView):
    model = Country
    template_name = 'geography/country_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:country-list')

@login_decorator
class CountryDeleteView(DeleteView):
    model = Country
    template_name = 'geography/country_confirm_delete.html'
    success_url = reverse_lazy('geography:country-list')

# NationalFederation
@login_decorator
class NationalFederationListView(ListView):
    model = NationalFederation
    template_name = 'geography/nationalfederation_list.html'
    context_object_name = 'nationalfederations'

@login_decorator
class NationalFederationDetailView(DetailView):
    model = NationalFederation
    template_name = 'geography/nationalfederation_detail.html'
    context_object_name = 'nationalfederation'

@login_decorator
class NationalFederationCreateView(CreateView):
    model = NationalFederation
    template_name = 'geography/nationalfederation_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:nationalfederation-list')

@login_decorator
class NationalFederationUpdateView(UpdateView):
    model = NationalFederation
    template_name = 'geography/nationalfederation_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:nationalfederation-list')

@login_decorator
class NationalFederationDeleteView(DeleteView):
    model = NationalFederation
    template_name = 'geography/nationalfederation_confirm_delete.html'
    success_url = reverse_lazy('geography:nationalfederation-list')

# Association
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

@login_decorator
class AssociationCreateView(CreateView):
    model = Association
    template_name = 'geography/association_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:association-list')

@login_decorator
class AssociationUpdateView(UpdateView):
    model = Association
    template_name = 'geography/association_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:association-list')

@login_decorator
class AssociationDeleteView(DeleteView):
    model = Association
    template_name = 'geography/association_confirm_delete.html'
    success_url = reverse_lazy('geography:association-list')

# Province
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

@login_decorator
class ProvinceCreateView(CreateView):
    model = Province
    template_name = 'geography/province_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:province-list')

@login_decorator
class ProvinceUpdateView(UpdateView):
    model = Province
    template_name = 'geography/province_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:province-list')

@login_decorator
class ProvinceDeleteView(DeleteView):
    model = Province
    template_name = 'geography/province_confirm_delete.html'
    success_url = reverse_lazy('geography:province-list')

# Region
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

@login_decorator
class RegionCreateView(CreateView):
    model = Region
    template_name = 'geography/region_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:region-list')

@login_decorator
class RegionUpdateView(UpdateView):
    model = Region
    template_name = 'geography/region_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:region-list')

@login_decorator
class RegionDeleteView(DeleteView):
    model = Region
    template_name = 'geography/region_confirm_delete.html'
    success_url = reverse_lazy('geography:region-list')

# Club
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

@login_decorator
class ClubCreateView(CreateView):
    model = Club
    template_name = 'geography/club_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:club-list')

@login_decorator
class ClubUpdateView(UpdateView):
    model = Club
    template_name = 'geography/club_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:club-list')

@login_decorator
class ClubDeleteView(DeleteView):
    model = Club
    template_name = 'geography/club_confirm_delete.html'
    success_url = reverse_lazy('geography:club-list')

# Membership
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

@login_decorator
class MembershipCreateView(CreateView):
    model = Membership
    template_name = 'geography/membership_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:membership-list')

@login_decorator
class MembershipUpdateView(UpdateView):
    model = Membership
    template_name = 'geography/membership_form.html'
    fields = '__all__'
    success_url = reverse_lazy('geography:membership-list')

@login_decorator
class MembershipDeleteView(DeleteView):
    model = Membership
    template_name = 'geography/membership_confirm_delete.html'
    success_url = reverse_lazy('geography:membership-list')