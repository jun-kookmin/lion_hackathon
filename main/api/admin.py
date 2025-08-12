from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html, mark_safe

from . import models

try:
    from django.contrib.gis.admin import OSMGeoAdmin as _GeoAdminBase
except Exception:
    _GeoAdminBase = admin.ModelAdmin


class PhotoInline(admin.TabularInline):
    model = models.Photo
    extra = 0
    fields = ("image", "uploaded_at")
    readonly_fields = ("uploaded_at",)


class RecommendationTagInline(admin.TabularInline):
    model = models.RecommendationTag
    extra = 0
    autocomplete_fields = ("tag",)


class FavoriteInline(admin.TabularInline):
    model = models.Favorite
    extra = 0
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at",)


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("uuid", "created_at", "analysis_requests_count", "favorites_count")
    search_fields = ("uuid",)
    readonly_fields = ("uuid", "created_at")
    ordering = ("-created_at",)

    def analysis_requests_count(self, obj):
        return obj.analysis_requests.count()

    def favorites_count(self, obj):
        return obj.favorites.count()


@admin.register(models.BusinessType)
class BusinessTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "children_count")
    search_fields = ("name",)
    list_filter = ("parent",)
    autocomplete_fields = ("parent",)
    ordering = ("id",)

    def children_count(self, obj):
        return obj.children.count()


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("id",)


@admin.register(models.Data)
class DataAdmin(_GeoAdminBase):
    """
    PointField를 지도 위젯으로 편집.
    PostGIS 아니어도 폴백되지만, 지도 기능은 gis admin 사용 시에만 활성화.
    """
    list_display = (
        "id", "address", "region", "monthly_rent", "deposit",
        "daily_footfall_avg", "allow_business_types_list", "tags_list",
    )
    list_filter = ("region", "allow_business_types", "tags")
    search_fields = ("address", "region")
    filter_horizontal = ("allow_business_types", "tags")
    ordering = ("id",)


    if _GeoAdminBase is not admin.ModelAdmin:
        default_lon = 127.0
        default_lat = 37.5665
        default_zoom = 11

    def allow_business_types_list(self, obj):
        return ", ".join(obj.allow_business_types.values_list("name", flat=True))

    def tags_list(self, obj):
        return ", ".join(obj.tags.values_list("name", flat=True))


@admin.register(models.AnalysisRequest)
class AnalysisRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "business_type", "plan", "address", "created_at")
    list_filter = ("plan", "business_type", "created_at")
    search_fields = ("user__uuid", "address")
    date_hierarchy = "created_at"
    autocomplete_fields = ("user", "business_type")
    inlines = [PhotoInline]
    ordering = ("-created_at",)


@admin.register(models.Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "analysis_request", "preview", "uploaded_at")
    list_filter = ("uploaded_at",)
    autocomplete_fields = ("analysis_request",)
    readonly_fields = ("uploaded_at",)
    ordering = ("-uploaded_at",)

    def preview(self, obj):
        if not obj.image:
            return "-"
        return format_html('<img src="{}" style="max-height:60px;"/>', obj.image.url)


@admin.register(models.Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = (
        "id", "analysis_request", "spot", "business_type",
        "score", "created_at", "tag_list",
    )
    list_filter = ("business_type", "created_at")
    search_fields = (
        "analysis_request__user__uuid", "spot__address", "business_type__name", "description",
    )
    autocomplete_fields = ("analysis_request", "spot", "business_type")
    readonly_fields = ("created_at",)
    inlines = [RecommendationTagInline, FavoriteInline]
    ordering = ("-score", "-id")

    def tag_list(self, obj):
        qs = models.Tag.objects.filter(recommendationtag__recommendation=obj)
        return ", ".join(qs.values_list("name", flat=True))


@admin.register(models.RecommendationTag)
class RecommendationTagAdmin(admin.ModelAdmin):
    list_display = ("id", "recommendation", "tag")
    search_fields = ("recommendation__id", "tag__name")
    autocomplete_fields = ("recommendation", "tag")
    ordering = ("id",)


@admin.register(models.Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recommendation", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__uuid", "recommendation__id")
    autocomplete_fields = ("user", "recommendation")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


admin.site.site_header = "상권 분석 Admin"
admin.site.site_title = "상권 분석 Admin"
admin.site.index_title = "대시보드"
