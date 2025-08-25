from rest_framework import viewsets
from .models import Province, Region, LocalFootballAssociation, Club, Association, NationalFederation, WorldSportsBody, Continent, ContinentFederation, ContinentRegion, Country
from .serializers import ProvinceSerializer, RegionSerializer, LocalFootballAssociationSerializer, ClubSerializer, AssociationSerializer, NationalFederationSerializer, WorldSportsBodySerializer, ContinentSerializer, ContinentFederationSerializer, ContinentRegionSerializer, CountrySerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view

class WorldSportsBodyViewSet(viewsets.ModelViewSet):
    queryset = WorldSportsBody.objects.all()
    serializer_class = WorldSportsBodySerializer

class ContinentViewSet(viewsets.ModelViewSet):
    queryset = Continent.objects.all()
    serializer_class = ContinentSerializer

class ContinentFederationViewSet(viewsets.ModelViewSet):
    queryset = ContinentFederation.objects.all()
    serializer_class = ContinentFederationSerializer

class ContinentRegionViewSet(viewsets.ModelViewSet):
    queryset = ContinentRegion.objects.all()
    serializer_class = ContinentRegionSerializer

class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

class NationalFederationViewSet(viewsets.ModelViewSet):
    queryset = NationalFederation.objects.all()
    serializer_class = NationalFederationSerializer

class ProvinceViewSet(viewsets.ModelViewSet):
    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer

class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

class AssociationViewSet(viewsets.ModelViewSet):
    queryset = Association.objects.all()
    serializer_class = AssociationSerializer

class LocalFootballAssociationViewSet(viewsets.ModelViewSet):
    queryset = LocalFootballAssociation.objects.all()
    serializer_class = LocalFootballAssociationSerializer

class ClubViewSet(viewsets.ModelViewSet):
    queryset = Club.objects.all()
    serializer_class = ClubSerializer

@api_view(['GET'])
def get_organizations(request, org_type):
    model_map = {
        'provinces': Province,
        'regions': Region,
        'lfas': LocalFootballAssociation,
        'clubs': Club,
    }
    model = model_map.get(org_type)
    if not model:
        return Response(status=404)

    queryset = model.objects.all()

    # Filtering
    province_id = request.query_params.get('province')
    if province_id and org_type == 'regions':
        queryset = queryset.filter(province_id=province_id)

    region_id = request.query_params.get('region')
    if region_id and org_type == 'lfas':
        queryset = queryset.filter(region_id=region_id)

    lfa_id = request.query_params.get('lfa')
    if lfa_id and org_type == 'clubs':
        queryset = queryset.filter(localfootballassociation_id=lfa_id)

    country_id = request.query_params.get('country')
    if country_id and org_type == 'provinces':
        queryset = queryset.filter(national_federation__country_id=country_id)


    serializer_class_map = {
        'provinces': ProvinceSerializer,
        'regions': RegionSerializer,
        'lfas': LocalFootballAssociationSerializer,
        'clubs': ClubSerializer,
    }
    serializer_class = serializer_class_map.get(org_type)
    serializer = serializer_class(queryset, many=True)
    return Response(serializer.data)
