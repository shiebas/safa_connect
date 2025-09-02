# Standard library imports
import datetime

# Third-party imports (Django)
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from rest_framework import viewsets

# Local application imports
from .forms import (
    AssociationForm, ClubForm, ContinentFederationForm, ContinentRegionForm,
    CountryForm, LocalFootballAssociationForm, NationalFederationForm,
    ProvinceForm, RegionForm, WorldSportsBodyForm, ClubRegistrationForm,
    ClubComplianceForm, ClubLogoForm
)
from .models import (
    Association, Club, Continent, ContinentFederation, ContinentRegion,
    Country, LocalFootballAssociation, NationalFederation, Province, Region,
    WorldSportsBody
)
from .serializers import (
    WorldSportsBodySerializer, ContinentSerializer, ContinentFederationSerializer, ContinentRegionSerializer, CountrySerializer, NationalFederationSerializer, ProvinceSerializer, RegionSerializer, AssociationSerializer, LocalFootballAssociationSerializer, ClubSerializer
)
from .permissions import (
    IsClubAdminOrReadOnly, IsLFAViewOnly, IsRegionViewOnly, IsProvinceViewOnly, IsNationalViewOnly
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
    context_object_name = 'worldsportsbody'
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
        return NationalFederation.objects.all()

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
        return Province.objects.select_related('national_federation')

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
    
    def get_success_url(self):
        # Redirect back to provincial admin dashboard if user came from there
        if self.request.user.role == 'ADMIN_PROVINCE':
            return reverse_lazy('accounts:provincial_admin_dashboard')
        # Default fallback to province list
        return reverse_lazy('geography:province-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Province created successfully.')
        return super().form_valid(form)

@login_decorator
class ProvinceUpdateView(LoginRequiredMixin, UpdateView):
    model = Province
    form_class = ProvinceForm
    template_name = 'geography/province_form.html'
    
    def get_success_url(self):
        # Debug logging
        print(f"DEBUG: ProvinceUpdateView get_success_url called for user: {self.request.user.email}")
        print(f"DEBUG: User role: {self.request.user.role}")
        print(f"DEBUG: Is ADMIN_PROVINCE: {self.request.user.role == 'ADMIN_PROVINCE'}")
        
        # Redirect back to provincial admin dashboard if user came from there
        if self.request.user.role == 'ADMIN_PROVINCE':
            print(f"DEBUG: Redirecting to provincial admin dashboard")
            return reverse_lazy('accounts:provincial_admin_dashboard')
        # Default fallback to province list
        print(f"DEBUG: Redirecting to province list")
        return reverse_lazy('geography:province-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Province updated successfully.')
        # Force redirect for provincial admins
        if self.request.user.role == 'ADMIN_PROVINCE':
            print(f"DEBUG: Force redirect in form_valid to provincial admin dashboard")
            from django.shortcuts import redirect
            return redirect('accounts:provincial_admin_dashboard')
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
        ).select_related('national_federation').order_by('name')

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
    
    def get_success_url(self):
        # Redirect back to provincial admin dashboard if user came from there
        if self.request.user.role == 'ADMIN_PROVINCE':
            return reverse_lazy('accounts:provincial_admin_dashboard')
        # Default fallback to region list
        return reverse_lazy('geography:region-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Region created successfully.')
        return super().form_valid(form)

@login_decorator
class RegionUpdateView(LoginRequiredMixin, UpdateView):
    model = Region
    form_class = RegionForm
    template_name = 'geography/region_form.html'
    
    def get_success_url(self):
        # Debug logging
        print(f"DEBUG: get_success_url called for user: {self.request.user.email}")
        print(f"DEBUG: User role: {self.request.user.role}")
        print(f"DEBUG: Is ADMIN_PROVINCE: {self.request.user.role == 'ADMIN_PROVINCE'}")
        
        # Redirect back to provincial admin dashboard if user came from there
        if self.request.user.role == 'ADMIN_PROVINCE':
            print(f"DEBUG: Redirecting to provincial admin dashboard")
            return reverse_lazy('accounts:provincial_admin_dashboard')
        # Default fallback to region list
        print(f"DEBUG: Redirecting to region list")
        return reverse_lazy('geography:region-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Region updated successfully.')
        # Force redirect for provincial admins
        if self.request.user.role == 'ADMIN_PROVINCE':
            print(f"DEBUG: Force redirect in form_valid to provincial admin dashboard")
            from django.shortcuts import redirect
            return redirect('accounts:provincial_admin_dashboard')
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        # If user is LFA admin, set club's Nat/Prov/Reg/LFA from user
        if hasattr(user, 'local_federation') and user.role == 'ADMIN_LOCAL_FED':
            lfa = user.local_federation
            form.instance.localfootballassociation = lfa
            form.instance.region = lfa.region
            form.instance.province = lfa.region.province
        return super().form_valid(form)

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
        ).select_related('national_federation').order_by('name')
        
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

# Simple geography home view
def geography_home(request):
    """Home page for geography app"""
    provinces = Province.objects.all()
    context = {
        'provinces': provinces,
        'title': 'Geography Management'
    }
    return render(request, 'geography/geography_home.html', context)

# API endpoints for registration form
def get_regions(request):
    """API endpoint to get regions filtered by province (query param)"""
    province_id = request.GET.get('province')
    if province_id:
        regions = Region.objects.filter(province_id=province_id).values('id', 'name')
        return JsonResponse(list(regions), safe=False)
    return JsonResponse([], safe=False)

def get_lfas(request):
    """API endpoint to get LFAs filtered by region (query param)"""
    region_id = request.GET.get('region')
    if region_id:
        lfas = LocalFootballAssociation.objects.filter(region_id=region_id).values('id', 'name')
        return JsonResponse(list(lfas), safe=False)
    return JsonResponse([], safe=False)

# Alternative API endpoints with path parameters
@csrf_exempt
def regions_by_province(request, province_id):
    """Get regions for a specific province by ID"""
    try:
        print(f"DEBUG: regions_by_province called with province_id: {province_id}")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Request path: {request.path}")
        
        province = get_object_or_404(Province, pk=province_id)
        print(f"DEBUG: Found province: {province.name}")
        
        regions = Region.objects.filter(
            province=province
        ).values('id', 'name').order_by('name')
        
        print(f"DEBUG: Found {regions.count()} regions")
        regions_list = list(regions)
        print(f"DEBUG: Regions data: {regions_list}")
        
        return JsonResponse(regions_list, safe=False)
    except Exception as e:
        print(f"DEBUG: Error in regions_by_province: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def lfas_by_region(request, region_id):
    """Get LFAs for a specific region by ID"""
    try:
        region = get_object_or_404(Region, pk=region_id)
        lfas = LocalFootballAssociation.objects.filter(
            region=region
        ).values('id', 'name').order_by('name')
        return JsonResponse(list(lfas), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def clubs_by_lfa(request, lfa_id):
    """Get clubs for a specific LFA by ID"""
    try:
        lfa = get_object_or_404(LocalFootballAssociation, pk=lfa_id)
        clubs = Club.objects.filter(
            localfootballassociation=lfa
        ).values('id', 'name').order_by('name')
        return JsonResponse(list(clubs), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# Debug view to test data
@csrf_exempt
def debug_geography_data(request):
    """Debug view to check geography data"""
    try:
        provinces = Province.objects.all().count()
        regions = Region.objects.all().count()
        lfas = LocalFootballAssociation.objects.all().count()
        clubs = Club.objects.all().count()
        
        # Get a sample province with regions
        sample_province = Province.objects.first()
        if sample_province:
            sample_regions = Region.objects.filter(province=sample_province).count()
            sample_province_name = sample_province.name
        else:
            sample_regions = 0
            sample_province_name = "None"
        
        debug_data = {
            'total_provinces': provinces,
            'total_regions': regions,
            'total_lfas': lfas,
            'total_clubs': clubs,
            'sample_province': sample_province_name,
            'sample_province_regions': sample_regions
        }
        
        return JsonResponse(debug_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# For API compatibility, add these as aliases
api_regions = get_regions
api_lfas = get_lfas

# Add back the hierarchical navigation functions that templates expect
@login_required
def province_regions(request, province_id):
    """Display regions within a specific province"""
    province = get_object_or_404(Province, id=province_id)
    regions = Region.objects.filter(province=province).order_by('name')
    context = {
        'province': province,
        'regions': regions,
        'regions_count': regions.count(),  # Add count for template
    }
    return render(request, 'geography/province_regions.html', context)

@login_required
def region_lfas(request, region_id):
    """Display LFAs within a specific region"""
    region = get_object_or_404(Region, id=region_id)
    lfas = LocalFootballAssociation.objects.filter(region=region).order_by('name')
    context = {
        'region': region,
        'lfas': lfas,
        'lfas_count': lfas.count(),  # Add count for template
    }
    return render(request, 'geography/region_lfas.html', context)

@login_required
def lfa_clubs(request, lfa_id):
    """Display clubs within a specific LFA"""
    lfa = get_object_or_404(LocalFootballAssociation, id=lfa_id)
    clubs = Club.objects.filter(localfootballassociation=lfa).order_by('name')
    context = {
        'lfa': lfa,
        'clubs': clubs,
        'clubs_count': clubs.count(),  # Add count for template
    }
    return render(request, 'geography/lfa_clubs.html', context)

# Add a debug view to check the data relationships
@login_required
def debug_province_regions(request):
    """Debug view to check province-region relationships"""
    provinces = Province.objects.all().order_by('name')
    debug_data = []
    total_regions = 0
    duplicates = []
    
    for province in provinces:
        regions = Region.objects.filter(province=province).order_by('created', 'name')
        region_list = list(regions.values('id', 'name', 'safa_id', 'created'))
        total_regions += regions.count()
        
        # Check for duplicates within this province
        region_names = {}
        province_duplicates = []
        for region in region_list:
            name = region['name']
            if name in region_names:
                # Found duplicate
                duplicate_info = {
                    'name': name,
                    'original': region_names[name],
                    'duplicate': region
                }
                province_duplicates.append(duplicate_info)
                duplicates.append(duplicate_info)
            else:
                region_names[name] = region
        
        debug_data.append({
            'province': province,
            'regions': region_list,
            'region_count': regions.count(),
            'duplicates': province_duplicates
        })
    
    all_regions = Region.objects.all().count()
    
    context = {
        'debug_data': debug_data,
        'title': 'Debug: Province-Region Relationships',
        'total_regions': total_regions,
        'all_regions_count': all_regions,
        'duplicates': duplicates,
    }
    return render(request, 'geography/debug_province_regions.html', context)

@login_required
def fix_duplicate_regions(request):
    """Fix duplicate regions by removing the newer ones"""
    if request.method == 'POST':
        duplicates_fixed = 0
        
        # Get all provinces
        provinces = Province.objects.all()
        
        for province in provinces:
            # Get regions grouped by name
            regions = Region.objects.filter(province=province).order_by('name', 'created')
            
            region_groups = {}
            for region in regions:
                if region.name not in region_groups:
                    region_groups[region.name] = []
                region_groups[region.name].append(region)
            
            # For each group with duplicates, keep the first (oldest) and delete the rest
            for name, region_list in region_groups.items():
                if len(region_list) > 1:
                    # Keep the first (oldest) region
                    regions_to_delete = region_list[1:]
                    
                    for duplicate_region in regions_to_delete:
                        # Move any LFAs from duplicate to the original region
                        original_region = region_list[0]
                        lfas = LocalFootballAssociation.objects.filter(region=duplicate_region)
                        lfas.update(region=original_region)
                        
                        # Delete the duplicate
                        duplicate_region.delete()
                        duplicates_fixed += 1
        
        messages.success(request, f'Fixed {duplicates_fixed} duplicate regions.')
        return redirect('geography:debug_province_regions')
    
    # Show confirmation page
    return render(request, 'geography/fix_duplicate_regions.html')

@login_required 
def club_list_view(request):
    """List all clubs with clean organization and pagination"""
    search_query = request.GET.get('search', '')
    lfa_filter = request.GET.get('lfa', '')
    region_filter = request.GET.get('region', '')
    province_filter = request.GET.get('province', '')
    
    clubs = Club.objects.select_related(
        'localfootballassociation__region__province'
    ).order_by('localfootballassociation__region__province__name', 'localfootballassociation__region__name', 'localfootballassociation__name', 'name')
    
    if search_query:
        clubs = clubs.filter(
            Q(name__icontains=search_query) |
            Q(localfootballassociation__name__icontains=search_query) |
            Q(localfootballassociation__region__name__icontains=search_query) |
            Q(localfootballassociation__region__province__name__icontains=search_query) |
            Q(safa_id__icontains=search_query)
        )
    
    if province_filter:
        clubs = clubs.filter(localfootballassociation__region__province_id=province_filter)
    
    if region_filter:
        clubs = clubs.filter(localfootballassociation__region_id=region_filter)
        
    if lfa_filter:
        clubs = clubs.filter(localfootballassociation_id=lfa_filter)
    
    paginator = Paginator(clubs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    provinces = Province.objects.all().order_by('name')
    regions = Region.objects.all().order_by('province__name', 'name')
    lfas = LocalFootballAssociation.objects.all().order_by('region__province__name', 'region__name', 'name')
    
    if province_filter:
        regions = regions.filter(province_id=province_filter)
        lfas = lfas.filter(region__province_id=province_filter)
    
    if region_filter:
        lfas = lfas.filter(region_id=region_filter)
    
    context = {
        'page_obj': page_obj,
        'clubs': page_obj.object_list,
        'total_count': clubs.count(),
        'search_query': search_query,
        'province_filter': province_filter,
        'region_filter': region_filter,
        'lfa_filter': lfa_filter,
        'provinces': provinces,
        'regions': regions,
        'lfas': lfas,
        'title': 'Football Clubs',
    }
    return render(request, 'geography/club_list_clean.html', context)

# Function-based views to match the URL patterns
def province_list_view(request):
    """Function-based view for the province list"""
    # Create an instance of the class-based view and call its get method
    view = ProvinceListView.as_view()
    return view(request)

def region_list_view(request):
    """Function-based view for the region list"""
    # Create an instance of the class-based view and call its get method
    view = RegionListView.as_view()
    return view(request)

def lfa_list_view(request):
    """Function-based view for the LFA list"""
    # Create an instance of the class-based view and call its get method
    view = LocalFootballAssociationListView.as_view()
    return view(request)

def province_detail(request, pk):
    """Function-based view for province detail"""
    view = ProvinceDetailView.as_view()
    return view(request, pk=pk)

def region_detail(request, pk):
    """Function-based view for region detail"""
    view = RegionDetailView.as_view()
    return view(request, pk=pk)

def lfa_detail(request, pk):
    """Function-based view for LFA detail"""
    view = LocalFootballAssociationDetailView.as_view()
    return view(request, pk=pk)

def lfa_hierarchical_view(request):
    """Hierarchical view of LFAs"""
    provinces = Province.objects.prefetch_related(
        'region_set__localfootballassociation_set'
    ).all()
    
    context = {
        'provinces': provinces,
        'title': 'LFA Hierarchical View'
    }
    return render(request, 'geography/lfa_hierarchical.html', context)


@login_required
@permission_required('geography.add_club', raise_exception=True)
def register_club(request):
    if request.method == 'POST':
        form = ClubRegistrationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('geography:region-detail', pk=request.user.region.pk)
    else:
        form = ClubRegistrationForm(user=request.user)

    return render(request, 'geography/register_club.html', {'form': form})

@login_required
def club_compliance_update(request):
    club = getattr(request.user, 'club', None)
    if not club:
        messages.error(request, 'You are not associated with a club.')
        return redirect('accounts:profile')
    if request.method == 'POST':
        form = ClubComplianceForm(request.POST, request.FILES, instance=club)
        if form.is_valid():
            form.save()
            messages.success(request, 'Club compliance information updated successfully!')
            return redirect('geography:club_compliance_update')
    else:
        form = ClubComplianceForm(instance=club)
    return render(request, 'geography/club_compliance_form.html', {'form': form, 'club': club})

@login_required
def lfa_info_update(request):
    lfa = getattr(request.user, 'local_federation', None)
    if not lfa:
        messages.error(request, 'You are not associated with an LFA.')
        return redirect('accounts:profile')
    if request.method == 'POST':
        form = LocalFootballAssociationForm(request.POST, request.FILES, instance=lfa)
        if form.is_valid():
            form.save()
            messages.success(request, 'LFA information updated successfully!')
            return redirect('geography:lfa_info_update')
    else:
        form = LocalFootballAssociationForm(instance=lfa)
    return render(request, 'geography/lfa_info_form.html', {'form': form, 'lfa': lfa})

@login_required
def edit_club_logo(request):
    """View for club admins to edit their club's logo"""
    if not request.user.is_authenticated or request.user.role != 'CLUB_ADMIN':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('accounts:modern_home')
    
    if not request.user.club:
        messages.error(request, 'Your user profile is not linked to a club. Please contact support.')
        return redirect('accounts:modern_home')
    
    club = request.user.club
    
    if request.method == 'POST':
        form = ClubLogoForm(request.POST, request.FILES, instance=club)
        if form.is_valid():
            form.save()
            messages.success(request, 'Club logo updated successfully!')
            return redirect('accounts:modern_home')
    else:
        form = ClubLogoForm(instance=club)
    
    return render(request, 'geography/edit_club_logo.html', {
        'form': form,
        'club': club
    })