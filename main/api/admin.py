from django.contrib import admin
from .models import (
    User, BusinessType, AnalysisRequest,
    TypeRecommendation, SpotRecommendation,
    FavoriteType, FavoriteSpot
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id","uuid", "created_at")
    search_fields = ("uuid",)


@admin.register(BusinessType)
class BusinessTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(AnalysisRequest)
class AnalysisRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "business_type", "latitude", "longitude", "created_at")
    list_filter = ("created_at",)
    search_fields = ("address",)


@admin.register(TypeRecommendation)
class TypeRecommendationAdmin(admin.ModelAdmin):
    list_display = ("id", "analysis_request", "business_type", "score", "check_save", "description", "created_at")
    search_fields = ("description",)


@admin.register(SpotRecommendation)
class SpotRecommendationAdmin(admin.ModelAdmin):
    list_display = ("id", "analysis_request", "business_type", "score", "check_save", "description","created_at")
    search_fields = ("description",)


@admin.register(FavoriteType)
class FavoriteTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recommendation", "created_at")


@admin.register(FavoriteSpot)
class FavoriteSpotAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recommendation", "created_at")
