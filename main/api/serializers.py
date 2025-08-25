# api/serializers.py
from __future__ import annotations
from django.db import transaction
from rest_framework import serializers
from .models import (
    User, BusinessType, Data, AnalysisRequest,
    TypeRecommendation, SpotRecommendation, FavoriteType, FavoriteSpot
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "uuid", "created_at"]
        read_only_fields = ["id", "created_at"]

class BusinessTypeSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(queryset=BusinessType.objects.all(), allow_null=True, required=False)
    class Meta:
        model = BusinessType
        fields = ["id", "name", "parent"]

class DataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Data
        fields = [
            "id", "code", "business_code", "business_types",
            "address", "region_code", "region", "floor",
            "latitude", "longitude", "monthly_rent", "deposit", "daily_footfall_avg",
        ]
        read_only_fields = ["id"]

class AnalysisRequestSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    business_type = serializers.PrimaryKeyRelatedField(queryset=BusinessType.objects.all(), allow_null=True, required=False)

    class Meta:
        model = AnalysisRequest
        fields = ["id", "user", "business_type", "plan", "latitude", "longitude", "address", "created_at", ]
        read_only_fields = ["id", "created_at"]

class TypeRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeRecommendation
        fields = ["id", "analysis_request", "business_type", "score", "description", "created_at"]
        read_only_fields = ["id", "created_at"]

class SpotRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpotRecommendation
        fields = ["id", "analysis_request", "spot", "business_type", "score", "description", "created_at"]
        read_only_fields = ["id", "created_at"]

class FavoriteTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteType
        fields = ["id", "user", "recommendation", "created_at"]
        read_only_fields = ["id", "created_at"]

class FavoriteSpotSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteSpot
        fields = ["id", "user", "recommendation", "created_at"]
        read_only_fields = ["id", "created_at"]
