# Standard library imports
import datetime

# Third-party imports (Django)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

# Local application imports
from .forms import (
    AssociationForm, ClubForm, ContinentFederationForm, ContinentRegionForm,
    CountryForm, LocalFootballAssociationForm, NationalFederationForm,
    ProvinceForm, RegionForm, WorldSportsBodyForm
)
from .models import (
    Association, Club, Continent, ContinentFederation, ContinentRegion,
    Country, LocalFootballAssociation, NationalFederation, Province, Region,
    WorldSportsBody
)

# Mixin to restrict access to staff users only
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


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
@login_decorator
class WorldSportsBodyListView(LoginRequiredMixin, ListView):
    model = WorldSportsBody
    context_object_name = 'world_bodies'
    template_name = 'geography/worldsportsbody_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(sport_code__icontains=q)
        return queryset

class WorldSportsBodyDetailView(LoginRequiredMixin, DetailView):
    model = WorldSportsBody
    context_object_name = 'world_body'
    template_name = 'geography/worldsportsbody_detail.html'

class WorldSportsBodyCreateView(LoginRequiredMixin, CreateView):
    model = WorldSportsBody
    form_class = WorldSportsBodyForm
    template_name = 'geography/worldsportsbody_form.html'
    success_url = reverse_lazy('geography:worldsportsbody-list')  # if using hyphens
    
    def form_valid(self, form):
        messages.success(self.request, 'World Sports Body created successfully.')
        return super().form_valid(form)

class WorldSportsBodyUpdateView(LoginRequiredMixin, UpdateView):
    model = WorldSportsBody
    form_class = WorldSportsBodyForm
    template_name = 'geography/worldsportsbody_form.html'
    success_url = reverse_lazy('geography:worldsportsbody-list')  # if using hyphens
    
    def form_valid(self, form):
        messages.success(self.request, 'World Sports Body updated successfully.')
        return super().form_valid(form)

class WorldSportsBodyDeleteView(LoginRequiredMixin, DeleteView):
    model = WorldSportsBody
    template_name = 'geography/worldsportsbody_confirm_delete.html'
    success_url = reverse_lazy('geography:worldsportsbody-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'World Sports Body deleted successfully.')
        return super().delete(request, *args, **kwargs)

# Continent
@login_decorator
class ContinentListView(ListView):
    model = Continent
    template_name = 'geography/continent_list.html'
    context_object_name = 'continents'
    paginate_by = 20

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
    context_object_name = 'continentfederations'
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
    success_url = reverse_lazy('geography:continentfederation-list')

    def form_valid(self, form):
        messages.success(self.request, 'Continent Federation created successfully!')
        return super().form_valid(form)

@login_decorator
class ContinentFederationUpdateView(UpdateView):
    model = ContinentFederation
    form_class = ContinentFederationForm
    template_name = 'geography/continentfederation_form.html'
    success_url = reverse_lazy('geography:continentfederation-list')

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
class ContinentRegionListView(LoginRequiredMixin, ListView):
    model = ContinentRegion
    context_object_name = 'continentregions'
    template_name = 'geography/continentregion_list.html'
    paginate_by = 10  # Add pagination
    
    def get_queryset(self):
        return ContinentRegion.objects.select_related('continent')

@login_decorator
class ContinentRegionCreateView(LoginRequiredMixin, CreateView):
    model = ContinentRegion
    form_class = ContinentRegionForm
    template_name = 'geography/continentregion_form.html'
    success_url = reverse_lazy('geography:continentregion-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Continent Region created successfully.')
        return super().form_valid(form)

@login_decorator
class ContinentRegionUpdateView(LoginRequiredMixin, UpdateView):
    model = ContinentRegion
    form_class = ContinentRegionForm
    template_name = 'geography/continentregion_form.html'
    success_url = reverse_lazy('geography:continentregion-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Continent Region updated successfully.')
        return super().form_valid(form)

class ContinentRegionDetailView(LoginRequiredMixin, DetailView):
    model = ContinentRegion
    context_object_name = 'region'
    template_name = 'geography/continentregion_detail.html'

@login_decorator
class ContinentRegionDeleteView(LoginRequiredMixin, DeleteView):
    model = ContinentRegion
    template_name = 'geography/continentregion_confirm_delete.html'
    success_url = reverse_lazy('geography:continentregion-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Continent Region deleted successfully.')
        return super().delete(request, *args, **kwargs)

# Country
@login_decorator
class CountryListView(LoginRequiredMixin, ListView):
    model = Country
    context_object_name = 'countries'
    template_name = 'geography/country_list.html'
    paginate_by = 10  # Add pagination
    
    def get_queryset(self):
        return Country.objects.select_related('continent_region')

@login_decorator
class CountryDetailView(LoginRequiredMixin, DetailView):
    model = Country
    context_object_name = 'country'
    template_name = 'geography/country_detail.html'

@login_decorator
class CountryCreateView(LoginRequiredMixin, CreateView):
    model = Country
    form_class = CountryForm
    template_name = 'geography/country_form.html'
    success_url = reverse_lazy('geography:country-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Country created successfully.')
        return super().form_valid(form)

@login_decorator
class CountryUpdateView(LoginRequiredMixin, UpdateView):
    model = Country
    form_class = CountryForm
    template_name = 'geography/country_form.html'
    success_url = reverse_lazy('geography:country-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Country updated successfully.')
        return super().form_valid(form)

@login_decorator
class CountryDeleteView(LoginRequiredMixin, DeleteView):
    model = Country
    template_name = 'geography/country_confirm_delete.html'
    success_url = reverse_lazy('geography:country-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Country deleted successfully.')
        return super().delete(request, *args, **kwargs)

# NationalFederation
@login_decorator
class NationalFederationListView(LoginRequiredMixin, ListView):
    model = NationalFederation
    context_object_name = 'federations'
    template_name = 'geography/nationalfederation_list.html'
    paginate_by = 10  # Add pagination
    
    def get_queryset(self):
        return NationalFederation.objects.select_related('country')

@login_decorator
class NationalFederationDetailView(LoginRequiredMixin, DetailView):
    model = NationalFederation
    context_object_name = 'federation'
    template_name = 'geography/nationalfederation_detail.html'

@login_decorator
class NationalFederationCreateView(LoginRequiredMixin, CreateView):
    model = NationalFederation
    form_class = NationalFederationForm
    template_name = 'geography/nationalfederation_form.html'
    success_url = reverse_lazy('geography:nationalfederation-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'National Federation created successfully.')
        return super().form_valid(form)

@login_decorator
class NationalFederationUpdateView(LoginRequiredMixin, UpdateView):
    model = NationalFederation
    form_class = NationalFederationForm
    template_name = 'geography/nationalfederation_form.html'
    success_url = reverse_lazy('geography:nationalfederation-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'National Federation updated successfully.')
        return super().form_valid(form)

@login_decorator
class NationalFederationDeleteView(LoginRequiredMixin, DeleteView):
    model = NationalFederation
    template_name = 'geography/nationalfederation_confirm_delete.html'
    success_url = reverse_lazy('geography:nationalfederation-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'National Federation deleted successfully.')
        return super().delete(request, *args, **kwargs)

# Association
@login_decorator
class AssociationListView(LoginRequiredMixin, ListView):
    model = Association
    context_object_name = 'associations'
    template_name = 'geography/association_list.html'
    paginate_by = 10  # Add pagination
    
    def get_queryset(self):
        return Association.objects.select_related('national_federation')

@login_decorator
class AssociationDetailView(LoginRequiredMixin, DetailView):
    model = Association
    context_object_name = 'association'
    template_name = 'geography/association_detail.html'

@login_decorator
class AssociationCreateView(LoginRequiredMixin, CreateView):
    model = Association
    form_class = AssociationForm
    template_name = 'geography/association_form.html'
    success_url = reverse_lazy('geography:association-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Association created successfully.')
        return super().form_valid(form)

@login_decorator
class AssociationUpdateView(LoginRequiredMixin, UpdateView):
    model = Association
    form_class = AssociationForm
    template_name = 'geography/association_form.html'
    success_url = reverse_lazy('geography:association-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Association updated successfully.')
        return super().form_valid(form)

@login_decorator
class AssociationDeleteView(LoginRequiredMixin, DeleteView):
    model = Association
    template_name = 'geography/association_confirm_delete.html'
    success_url = reverse_lazy('geography:association-list')
    context_object_name = 'object'
    
    def delete(self, request, *args, **kwargs):
        try:
            messages.success(request, 'Association deleted successfully.')
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f"Error deleting association: {str(e)}")
            return redirect('geography:association-list')

# Province
@login_decorator
class ProvinceListView(LoginRequiredMixin, ListView):
    model = Province
    context_object_name = 'provinces'
    template_name = 'geography/province_list.html'
    paginate_by = 10  # Add pagination
    
    def get_queryset(self):
        return Province.objects.select_related('country')

@login_decorator
class ProvinceDetailView(LoginRequiredMixin, DetailView):
    model = Province
    template_name = 'geography/province_detail.html'
    context_object_name = 'province'

@login_decorator
class ProvinceCreateView(LoginRequiredMixin, CreateView):
    model = Province
    form_class = ProvinceForm
    template_name = 'geography/province_form.html'
    success_url = reverse_lazy('geography:province-list')

    def form_valid(self, form):
        messages.success(self.request, 'Province created successfully.')
        return super().form_valid(form)

@login_decorator
class ProvinceUpdateView(LoginRequiredMixin, UpdateView):
    model = Province
    form_class = ProvinceForm
    template_name = 'geography/province_form.html'
    success_url = reverse_lazy('geography:province-list')

    def form_valid(self, form):
        messages.success(self.request, 'Province updated successfully.')
        return super().form_valid(form)

@login_decorator
class ProvinceDeleteView(LoginRequiredMixin, DeleteView):
    model = Province
    template_name = 'geography/province_confirm_delete.html'
    success_url = reverse_lazy('geography:province-list')
    context_object_name = 'object'
    
    def delete(self, request, *args, **kwargs):
        try:
            messages.success(request, 'Province deleted successfully.')
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f"Error deleting province: {str(e)}")
            return redirect('geography:province-list')

# Region
@login_decorator
class RegionListView(LoginRequiredMixin, ListView):
    model = Region
    context_object_name = 'provinces_with_regions'  # Changed to receive grouped data
    template_name = 'geography/region_list.html'
    paginate_by = 10  # Set pagination to 10 items

    def get_queryset(self):
        # Get all provinces with their regions, LFAs, and clubs in a hierarchical structure
        provinces = Province.objects.prefetch_related(
            Prefetch('region_set', queryset=Region.objects.all()),
            Prefetch(
                'region_set__localfootballassociation_set', 
                queryset=LocalFootballAssociation.objects.all().select_related('association')
            ),
            Prefetch(
                'region_set__localfootballassociation_set__clubs',  # <-- changed from club_set to clubs
                queryset=Club.objects.all()
            )
        ).select_related('country').order_by('name')

        return provinces

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Calculate club counts for each province and region
        provinces_with_counts = []
        for province in context['provinces_with_regions']:
            region_data = []
            province_club_count = 0

            for region in province.region_set.all():
                region_club_count = sum(lfa.clubs.count() for lfa in region.localfootballassociation_set.all())  # <-- changed from club_set to clubs
                province_club_count += region_club_count

                region_data.append({
                    'region': region,
                    'club_count': region_club_count
                })

            provinces_with_counts.append({
                'province': province,
                'regions': region_data,
                'club_count': province_club_count
            })

        context['provinces_with_counts'] = provinces_with_counts
        return context

@login_decorator
class RegionCreateView(LoginRequiredMixin, CreateView):
    model = Region
    form_class = RegionForm
    template_name = 'geography/region_form.html'
    success_url = reverse_lazy('geography:region-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Region created successfully.')
        return super().form_valid(form)

@login_decorator
class RegionUpdateView(LoginRequiredMixin, UpdateView):
    model = Region
    form_class = RegionForm
    template_name = 'geography/region_form.html'
    success_url = reverse_lazy('geography:region-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Region updated successfully.')
        return super().form_valid(form)

class RegionDetailView(LoginRequiredMixin, DetailView):
    model = Region
    context_object_name = 'region'
    template_name = 'geography/region_detail.html'

class RegionDeleteView(LoginRequiredMixin, DeleteView):
    model = Region
    template_name = 'geography/region_confirm_delete.html'
    success_url = reverse_lazy('geography:region-list')
    context_object_name = 'object'
    
    def delete(self, request, *args, **kwargs):
        try:
            messages.success(request, 'Region deleted successfully.')
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f"Error deleting region: {str(e)}")
            return redirect('geography:region-list')

# Club
@login_decorator
class ClubListView(LoginRequiredMixin, ListView):
    model = Club
    template_name = "geography/club_list.html"
    context_object_name = "clubs"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provinces_with_counts = []
        provinces = Province.objects.prefetch_related(
            'region_set__localfootballassociation_set__clubs'
        ).all()
        for province in provinces:
            region_data = []
            province_club_count = 0
            for region in province.region_set.all():
                region_club_count = 0
                for lfa in region.localfootballassociation_set.all():
                    club_count = lfa.clubs.count()
                    region_club_count += club_count
                province_club_count += region_club_count
                region_data.append({
                    'region': region,
                    'club_count': region_club_count
                })
            provinces_with_counts.append({
                'province': province,
                'regions': region_data,
                'club_count': province_club_count
            })
        context['provinces_with_counts'] = provinces_with_counts
        return context

@login_decorator
class ClubCreateView(LoginRequiredMixin, CreateView):
    model = Club
    form_class = ClubForm
    template_name = 'geography/club_form.html'
    success_url = reverse_lazy('geography:club-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Club created successfully.')
        return response

class ClubUpdateView(LoginRequiredMixin, UpdateView):
    model = Club
    form_class = ClubForm
    template_name = 'geography/club_form.html'
    success_url = reverse_lazy('geography:club-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Club updated successfully.')
        return response

class ClubDetailView(LoginRequiredMixin, DetailView):
    model = Club
    context_object_name = 'club'
    template_name = 'geography/club_detail.html'

class ClubDeleteView(LoginRequiredMixin, DeleteView):
    model = Club
    template_name = 'geography/club_confirm_delete.html'
    success_url = reverse_lazy('geography:club-list')
    context_object_name = 'object'
    
    def delete(self, request, *args, **kwargs):
        try:
            messages.success(request, 'Club deleted successfully.')
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f"Error deleting club: {str(e)}")
            return redirect('geography:club-list')

# LocalFootballAssociation
@login_decorator
class LocalFootballAssociationListView(LoginRequiredMixin, ListView):
    model = LocalFootballAssociation
    context_object_name = 'provinces_with_regions'
    template_name = 'geography/localfootballassociation_list.html'
    paginate_by = 10
    
    def get_queryset(self):
        # Get all provinces with their regions
        provinces = Province.objects.prefetch_related(
            Prefetch('region_set', queryset=Region.objects.all()),
            Prefetch(
                'region_set__localfootballassociation_set', 
                queryset=LocalFootballAssociation.objects.all().select_related('association')
            )
        ).select_related('country').order_by('name')
        
        return provinces
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate the LFA count for each province
        provinces_with_counts = []
        for province in context['provinces_with_regions']:
            lfa_count = sum(region.localfootballassociation_set.count() for region in province.region_set.all())
            provinces_with_counts.append({
                'province': province,
                'lfa_count': lfa_count
            })
        
        context['provinces_with_counts'] = provinces_with_counts
        return context

@login_decorator
class LocalFootballAssociationCreateView(LoginRequiredMixin, CreateView):
    model = LocalFootballAssociation
    form_class = LocalFootballAssociationForm
    template_name = 'geography/localfootballassociation_form.html'
    success_url = reverse_lazy('geography:localfootballassociation-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Local Football Association created successfully.')
        return super().form_valid(form)

@login_decorator
class LocalFootballAssociationUpdateView(LoginRequiredMixin, UpdateView):
    model = LocalFootballAssociation
    form_class = LocalFootballAssociationForm
    template_name = 'geography/localfootballassociation_form.html'
    success_url = reverse_lazy('geography:localfootballassociation-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Local Football Association updated successfully.')
        return super().form_valid(form)

class LocalFootballAssociationDetailView(LoginRequiredMixin, DetailView):
    model = LocalFootballAssociation
    context_object_name = 'lfa'
    template_name = 'geography/localfootballassociation_detail.html'

@login_decorator
class LocalFootballAssociationDeleteView(LoginRequiredMixin, DeleteView):
    model = LocalFootballAssociation
    template_name = 'geography/localfootballassociation_confirm_delete.html'
    success_url = reverse_lazy('geography:localfootballassociation-list')
    context_object_name = 'object'
    
    def delete(self, request, *args, **kwargs):
        try:
            messages.success(request, 'Local Football Association deleted successfully.')
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f"Error deleting LFA: {str(e)}")
            return redirect('geography:localfootballassociation-list')

def get_regions_by_province(request):
    """API view to get regions for a selected province"""
    province_id = request.GET.get('province_id')
    if not province_id:
        return JsonResponse([], safe=False)
    
    regions = list(Region.objects.filter(
        province_id=province_id
    ).values('id', 'name'))
    
    return JsonResponse(regions, safe=False)

def get_lfas_by_region(request):
    """API view to get LFAs for a selected region"""
    region_id = request.GET.get('region_id')
    if not region_id:
        return JsonResponse([], safe=False)
    
    lfas = list(LocalFootballAssociation.objects.filter(
        region_id=region_id
    ).values('id', 'name'))
    
    return JsonResponse(lfas, safe=False)