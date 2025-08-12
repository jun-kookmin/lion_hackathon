from __future__ import annotations

from typing import List

from django.contrib.gis.geos import Point
from rest_framework import serializers

from . import models


class PointDictField(serializers.Field):

    def to_representation(self, value: Point | None):
        if value is None:
            return None
        return {"lng": value.x, "lat": value.y}

    def to_internal_value(self, data):
        if not isinstance(data, dict) or "lng" not in data or "lat" not in data:
            raise serializers.ValidationError("point은 {'lng': float, 'lat': float} 형태여야 합니다.")
        try:
            lng = float(data["lng"])
            lat = float(data["lat"])
        except (TypeError, ValueError):
            raise serializers.ValidationError("lng/lat는 숫자여야 합니다.")
        return Point(lng, lat, srid=4326)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ["uuid", "created_at"]
        read_only_fields = ["uuid", "created_at"]


class BusinessTypeSimpleSerializer(serializers.ModelSerializer):
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=models.BusinessType.objects.all(),
        source="parent",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = models.BusinessType
        fields = ["id", "name", "parent_id"]


class BusinessTypeDetailSerializer(BusinessTypeSimpleSerializer):
    children = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True
    )

    class Meta(BusinessTypeSimpleSerializer.Meta):
        fields = BusinessTypeSimpleSerializer.Meta.fields + ["children"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = ["id", "name"]

class DataSerializer(serializers.ModelSerializer):
    point = PointDictField()
    allow_business_types = serializers.PrimaryKeyRelatedField(
        queryset=models.BusinessType.objects.all(), many=True, required=False
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=models.Tag.objects.all(), many=True, required=False
    )

    allow_business_types_names = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name", source="allow_business_types"
    )
    tag_names = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name", source="tags"
    )

    class Meta:
        model = models.Data
        fields = [
            "id",
            "point",
            "address",
            "region",
            "allow_business_types",
            "tags",
            "monthly_rent",
            "deposit",
            "daily_footfall_avg",
            # read-only helpers
            "allow_business_types_names",
            "tag_names",
        ]

    def create(self, validated_data):
        abt = validated_data.pop("allow_business_types", [])
        tags = validated_data.pop("tags", [])
        obj = models.Data.objects.create(**validated_data)
        if abt:
            obj.allow_business_types.set(abt)
        if tags:
            obj.tags.set(tags)
        return obj

    def update(self, instance, validated_data):
        abt = validated_data.pop("allow_business_types", None)
        tags = validated_data.pop("tags", None)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if abt is not None:
            instance.allow_business_types.set(abt)
        if tags is not None:
            instance.tags.set(tags)
        return instance


class AnalysisRequestSerializer(serializers.ModelSerializer):
    point = PointDictField(required=False, allow_null=True)
    user = serializers.PrimaryKeyRelatedField(queryset=models.User.objects.all())
    business_type = serializers.PrimaryKeyRelatedField(
        queryset=models.BusinessType.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = models.AnalysisRequest
        fields = [
            "id",
            "user",
            "business_type",
            "plan",
            "point",
            "address",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Photo
        fields = ["id", "analysis_request", "image", "uploaded_at"]
        read_only_fields = ["uploaded_at"]



class RecommendationSerializer(serializers.ModelSerializer):
    analysis_request = serializers.PrimaryKeyRelatedField(
        queryset=models.AnalysisRequest.objects.all()
    )
    spot = serializers.PrimaryKeyRelatedField(queryset=models.Data.objects.all())
    business_type = serializers.PrimaryKeyRelatedField(
        queryset=models.BusinessType.objects.all()
    )


    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=models.Tag.objects.all(), many=True, write_only=True, required=False
    )
    tags = TagSerializer(many=True, read_only=True, source="get_tags")

    class Meta:
        model = models.Recommendation
        fields = [
            "id",
            "analysis_request",
            "spot",
            "business_type",
            "score",
            "description",
            "created_at",
            "tag_ids", 
            "tags",    
        ]
        read_only_fields = ["created_at"]


    def get_tags(self, obj):
        qs = models.Tag.objects.filter(recommendationtag__recommendation=obj)
        return qs

    def _set_tags(self, recommendation: models.Recommendation, tags: List[models.Tag]):
        models.RecommendationTag.objects.filter(recommendation=recommendation).delete()
        bulk = [
            models.RecommendationTag(recommendation=recommendation, tag=t) for t in tags
        ]
        if bulk:
            models.RecommendationTag.objects.bulk_create(bulk)

    def create(self, validated_data):
        tag_ids = validated_data.pop("tag_ids", [])
        rec = models.Recommendation.objects.create(**validated_data)
        if tag_ids:
            self._set_tags(rec, tag_ids)
        return rec

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop("tag_ids", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if tag_ids is not None:
            self._set_tags(instance, tag_ids)
        return instance


class RecommendationTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RecommendationTag
        fields = ["id", "recommendation", "tag"]


# --- Favorite ---
class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=models.User.objects.all())
    recommendation = serializers.PrimaryKeyRelatedField(
        queryset=models.Recommendation.objects.all()
    )

    class Meta:
        model = models.Favorite
        fields = ["id", "user", "recommendation", "created_at"]
        read_only_fields = ["created_at"]
