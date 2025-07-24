from django.http import JsonResponse
from geography.models import Region, LocalFootballAssociation, Club, Association

def regions_by_province(request, province_id):
    regions = Region.objects.filter(province_id=province_id).values('id', 'name')
    return JsonResponse(list(regions), safe=False)

def lfas_by_region(request, region_id):
    lfas = LocalFootballAssociation.objects.filter(region_id=region_id).values('id', 'name')
    return JsonResponse(list(lfas), safe=False)

def clubs_by_lfa(request, lfa_id):
    clubs = Club.objects.filter(localfootballassociation_id=lfa_id).values('id', 'name')
    return JsonResponse(list(clubs), safe=False)

def associations_by_lfa(request, lfa_id):
    associations = Association.objects.filter(local_football_association_id=lfa_id).values('id', 'name')
    return JsonResponse(list(associations), safe=False)