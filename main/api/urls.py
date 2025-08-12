from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'business-types', views.BusinessTypeViewSet, basename='businesstype')
router.register(r'tags', views.TagViewSet, basename='tag')
router.register(r'data', views.DataViewSet, basename='data')
router.register(r'analysis-requests', views.AnalysisRequestViewSet, basename='analysisrequest')
router.register(r'photos', views.PhotoViewSet, basename='photo')
router.register(r'recommendations', views.RecommendationViewSet, basename='recommendation')
router.register(r'recommendation-tags', views.RecommendationTagViewSet, basename='recommendationtag')
router.register(r'favorites', views.FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('', include(router.urls)),
]
