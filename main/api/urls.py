# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, BusinessTypeViewSet, DataViewSet,
    AnalysisRequestViewSet, TypeRecommendationViewSet, SpotRecommendationViewSet,
    FavoriteTypeViewSet, FavoriteSpotViewSet,
    RecommendBusinessTypes, RecommendSpotsByType
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"business-types", BusinessTypeViewSet, basename="business-type")
router.register(r"data", DataViewSet, basename="data")
router.register(r"analysis-requests", AnalysisRequestViewSet, basename="analysis-request")
router.register(r"type-recommendations", TypeRecommendationViewSet, basename="type-recommendation")
router.register(r"spot-recommendations", SpotRecommendationViewSet, basename="spot-recommendation")
router.register(r"favorite-types", FavoriteTypeViewSet, basename="favorite-type")
router.register(r"favorite-spots", FavoriteSpotViewSet, basename="favorite-spot")

urlpatterns = [
    path("", include(router.urls)),  # 여기에는 api/v1/ 안 붙임

    path("recommendations/types/", RecommendBusinessTypes.as_view(), name="recommend-types"),
    path("recommendations/spots/", RecommendSpotsByType.as_view(), name="recommend-spots-by-type"),
]
