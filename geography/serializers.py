from rest_framework import serializers
from .models import (
    WorldSportsBody, Continent, ContinentFederation, ContinentRegion, Country, NationalFederation, Province, Region, Association, LocalFootballAssociation, Club
)

class WorldSportsBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorldSportsBody
        fields = '__all__'

class ContinentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Continent
        fields = '__all__'

class ContinentFederationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContinentFederation
        fields = '__all__'

class ContinentRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContinentRegion
        fields = '__all__'

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'

class NationalFederationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NationalFederation
        fields = '__all__'

class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = '__all__'

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'

class AssociationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Association
        fields = '__all__'

class LocalFootballAssociationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalFootballAssociation
        fields = '__all__'

class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = '__all__'
