from __future__ import annotations
from django.db import transaction
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from . import models
from . import serializers as sz


class BasePerm(permissions.AllowAny):
    pass


class UserViewSet(viewsets.ModelViewSet):
    queryset = models.User.objects.all().order_by("-created_at")
    serializer_class = sz.UserSerializer
    permission_classes = [BasePerm]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["uuid"]
    ordering_fields = ["created_at"]


class BusinessTypeViewSet(viewsets.ModelViewSet):
    queryset = models.BusinessType.objects.all().select_related("parent")
    serializer_class = sz.BusinessTypeDetailSerializer
    permission_classes = [BasePerm]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["parent"]
    search_fields = ["name"]
    ordering_fields = ["id", "name"]


class TagViewSet(viewsets.ModelViewSet):
    queryset = models.Tag.objects.all()
    serializer_class = sz.TagSerializer
    permission_classes = [BasePerm]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["id", "name"]


class DataViewSet(viewsets.ModelViewSet):
    queryset = (
        models.Data.objects.all()
        .prefetch_related("allow_business_types", "tags")
        .order_by("id")
    )
    serializer_class = sz.DataSerializer
    permission_classes = [BasePerm]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["region", "allow_business_types", "tags"]
    search_fields = ["address", "region"]
    ordering_fields = ["monthly_rent", "deposit", "daily_footfall_avg", "id"]

    @action(detail=False, methods=["get"])
    def within(self, request):
        
        try:
            lng = float(request.query_params.get("lng"))
            lat = float(request.query_params.get("lat"))
            radius = float(request.query_params.get("radius", 1000))
        except (TypeError, ValueError):
            return Response({"detail": "lng/lat/radius 파라미터를 확인하세요."},
                            status=status.HTTP_400_BAD_REQUEST)

        # 위도 경도 1도 ≈ 111km 근사치로 bbox 필터 (데모용)
        ddeg = radius / 111_000.0
        qs = self.get_queryset().filter(
            point__x__gte=lng - ddeg,
            point__x__lte=lng + ddeg,
            point__y__gte=lat - ddeg,
            point__y__lte=lat + ddeg,
        )[:200]
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        return Response(self.get_serializer(qs, many=True).data)


class AnalysisRequestViewSet(viewsets.ModelViewSet):
    queryset = models.AnalysisRequest.objects.all().select_related("user", "business_type")
    serializer_class = sz.AnalysisRequestSerializer
    permission_classes = [BasePerm]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["plan", "user", "business_type"]
    ordering_fields = ["created_at"]


class PhotoViewSet(viewsets.ModelViewSet):
    queryset = models.Photo.objects.all().select_related("analysis_request")
    serializer_class = sz.PhotoSerializer
    permission_classes = [BasePerm]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["analysis_request"]
    ordering_fields = ["uploaded_at"]


class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = (
        models.Recommendation.objects.all()
        .select_related("analysis_request", "spot", "business_type")
        .order_by("-score", "-id")
    )
    serializer_class = sz.RecommendationSerializer
    permission_classes = [BasePerm]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["analysis_request", "business_type", "spot"]
    ordering_fields = ["score", "created_at"]

    @action(detail=True, methods=["post"])
    def set_tags(self, request, pk=None):
        """
        POST /api/v1/recommendations/{id}/set_tags
        body: {"tag_ids": [1,2,3]}
        """
        rec = self.get_object()
        tag_ids = request.data.get("tag_ids", [])
        if not isinstance(tag_ids, list):
            return Response({"detail": "tag_ids는 배열이어야 합니다."}, status=400)
        tags = models.Tag.objects.filter(id__in=tag_ids)
        ser = self.get_serializer(rec, data={"tag_ids": [t.id for t in tags]}, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=200)


class RecommendationTagViewSet(viewsets.ModelViewSet):
    queryset = models.RecommendationTag.objects.all().select_related("recommendation", "tag")
    serializer_class = sz.RecommendationTagSerializer
    permission_classes = [BasePerm]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["recommendation", "tag"]
    ordering_fields = ["id"]


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = models.Favorite.objects.all().select_related("user", "recommendation")
    serializer_class = sz.FavoriteSerializer
    permission_classes = [BasePerm]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["user", "recommendation"]
    ordering_fields = ["created_at"]
