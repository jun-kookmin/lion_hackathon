from __future__ import annotations

import math
from typing import List, Dict, Any
from collections import defaultdict

from django.db import transaction
from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    User, BusinessType, Data, AnalysisRequest,
    TypeRecommendation, SpotRecommendation,
    FavoriteType, FavoriteSpot,
)
from .serializers import (
    UserSerializer, BusinessTypeSerializer, DataSerializer, AnalysisRequestSerializer,
    TypeRecommendationSerializer, SpotRecommendationSerializer,
    FavoriteTypeSerializer, FavoriteSpotSerializer,
)

VISIT_RATE_BY_TYPE = {
    "편의점": 0.040,
    "카페": 0.035,
    "음식점": 0.050,
    "식당": 0.050,
    "미용": 0.015,
    "헤어": 0.015,
    "약국": 0.020,
}
DEFAULT_VISIT_RATE = 0.025

def get_visit_rate(btype: str | None) -> float:
    bt = (btype or "").strip()
    for k, v in VISIT_RATE_BY_TYPE.items():
        if k in bt:
            return float(v)
    return float(DEFAULT_VISIT_RATE)

def _int_or_none(x):
    try:
        return int(x) if x is not None else None
    except:
        return None
    
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
    return 2 * R * math.asin(math.sqrt(a))

def minmax(vals: List[float]):
    vals = [v for v in vals if v is not None]
    if not vals:
        return (0.0, 1.0)
    vmin, vmax = min(vals), max(vals)
    if vmax == vmin:
        return (vmin, vmax + 1e-9)
    return vmin, vmax

def norm(x, a, b):
    return (x - a) / (b - a) if b > a else 0.0

def _int_or_none(v):
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None

def _float_or_default(v, default):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

try:
    from api.services.llm_openai import explain as _llm_explain
except Exception:
    _llm_explain = None

def _fallback_explain(features: dict, lang: str = "ko") -> str:
    parts = []
    dk = features.get("distance_km")
    if dk is not None:
        try:
            parts.append(f"요청 지점에서 약 {round(float(dk), 2)}km")
        except Exception:
            pass

    foot_val = _int_or_none(features.get("daily_footfall_avg"))
    if foot_val is not None:
        parts.append(f"유동인구 {foot_val:,}명")

    rent_val = _int_or_none(features.get("monthly_rent"))
    if rent_val is not None:
        parts.append(f"월세 {rent_val:,}원")

    dep_val = _int_or_none(features.get("deposit"))
    if dep_val is not None:
        parts.append(f"보증금 {dep_val:,}원")

    fl = features.get("floor")
    if isinstance(fl, int) and fl in (1, 2, 3):
        parts.append(f"{fl}층")

    base = ", ".join(parts) if parts else "여러 지표가 균형적"
    return base + " 등을 종합해 상위 후보로 선정했습니다."

def safe_explain(features: dict, lang: str = "ko") -> str:
    if _llm_explain:
        try:
            return _llm_explain(features, lang=lang)
        except Exception:
            pass
    return _fallback_explain(features, lang)

class BaseModelViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

# Endpoints:
# GET    /api/v1/users
# POST   /api/v1/users
# GET    /api/v1/users/{id}
# PATCH  /api/v1/users/{id}
# DELETE /api/v1/users/{id}
class UserViewSet(BaseModelViewSet):
    queryset = User.objects.all().order_by("-id")
    serializer_class = UserSerializer
    filterset_fields = ["uuid"]
    search_fields = ["uuid"]
    ordering_fields = ["id", "created_at"]

# Endpoints:
# GET    /api/v1/business-types
# POST   /api/v1/business-types
# GET    /api/v1/business-types/{id}
# PATCH  /api/v1/business-types/{id}
# DELETE /api/v1/business-types/{id}
class BusinessTypeViewSet(BaseModelViewSet):
    queryset = BusinessType.objects.select_related("parent").all().order_by("id")
    serializer_class = BusinessTypeSerializer
    filterset_fields = ["name", "parent"]
    search_fields = ["name"]
    ordering_fields = ["id", "name"]

# Endpoints:
# GET    /api/v1/data
# POST   /api/v1/data
# GET    /api/v1/data/{id}
# PATCH  /api/v1/data/{id}
# DELETE /api/v1/data/{id}
class DataViewSet(BaseModelViewSet):
    queryset = Data.objects.all().order_by("id")
    serializer_class = DataSerializer
    filterset_fields = [
        "business_code", "business_types", "region_code", "region", "floor",
        "monthly_rent", "deposit",
    ]
    search_fields = ["business_code", "business_types", "address", "region"]
    ordering_fields = ["id", "monthly_rent", "deposit", "daily_footfall_avg", "latitude", "longitude"]

    # GET /api/v1/data/by_bbox?min_lat=&max_lat=&min_lon=&max_lon=
    @action(detail=False, methods=["get"])
    def by_bbox(self, request):
        try:
            min_lat = float(request.query_params.get("min_lat"))
            max_lat = float(request.query_params.get("max_lat"))
            min_lon = float(request.query_params.get("min_lon"))
            max_lon = float(request.query_params.get("max_lon"))
        except (TypeError, ValueError):
            return Response({"detail": "min/max_lat, min/max_lon 쿼리 파라미터 필요"}, status=400)

        qs = self.get_queryset().filter(
            latitude__gte=min_lat, latitude__lte=max_lat,
            longitude__gte=min_lon, longitude__lte=max_lon,
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)

# Endpoints:
# GET    /api/v1/analysis-requests
# POST   /api/v1/analysis-requests
# GET    /api/v1/analysis-requests/{id}
# PATCH  /api/v1/analysis-requests/{id}
# DELETE /api/v1/analysis-requests/{id}
class AnalysisRequestViewSet(BaseModelViewSet):
    queryset = AnalysisRequest.objects.select_related("user", "business_type").all()
    serializer_class = AnalysisRequestSerializer
    filterset_fields = ["user", "business_type"]
    search_fields = ["address", "user__uuid"]
    ordering_fields = ["id", "created_at"]

# Endpoints:
# GET    /api/v1/type-recommendations
# POST   /api/v1/type-recommendations
# GET    /api/v1/type-recommendations/{id}
# PATCH  /api/v1/type-recommendations/{id}
# DELETE /api/v1/type-recommendations/{id}
class TypeRecommendationViewSet(BaseModelViewSet):
    queryset = (
        TypeRecommendation.objects
        .select_related("analysis_request", "business_type")
        .all()
        .order_by("-score", "-id")
    )
    serializer_class = TypeRecommendationSerializer
    filterset_fields = ["analysis_request", "business_type"]
    search_fields = ["description", "business_type__name"]
    ordering_fields = ["score", "created_at", "id"]

    # GET /api/v1/type-recommendations/by_request?analysis_request=&limit=3
    @action(detail=False, methods=["get"])
    def by_request(self, request):
        try:
            ar_id = int(request.query_params.get("analysis_request"))
        except (TypeError, ValueError):
            return Response({"detail": "analysis_request 쿼리 파라미터가 필요합니다."}, status=400)
        limit_param = request.query_params.get("limit", "3")
        try:
            limit = max(1, min(50, int(limit_param)))
        except (TypeError, ValueError):
            limit = 3
        qs = self.get_queryset().filter(analysis_request_id=ar_id).order_by("-score", "-id")[:limit]
        return Response(self.get_serializer(qs, many=True).data)

# Endpoints:
# GET    /api/v1/spot-recommendations
# POST   /api/v1/spot-recommendations
# GET    /api/v1/spot-recommendations/{id}
# PATCH  /api/v1/spot-recommendations/{id}
# DELETE /api/v1/spot-recommendations/{id}
class SpotRecommendationViewSet(BaseModelViewSet):
    queryset = (
        SpotRecommendation.objects
        .select_related("analysis_request", "spot", "business_type")
        .all()
        .order_by("-score", "-id")
    )
    serializer_class = SpotRecommendationSerializer
    filterset_fields = ["analysis_request", "business_type", "spot"]
    search_fields = ["description", "spot__address", "spot__code", "business_type__name"]
    ordering_fields = ["score", "created_at", "id"]
    ordering = ["-created_at"]

    # GET /api/v1/spot-recommendations/by_request?analysis_request=&limit=3
    @action(detail=False, methods=["get"])
    def by_request(self, request):
        try:
            ar_id = int(request.query_params.get("analysis_request"))
        except (TypeError, ValueError):
            return Response({"detail": "analysis_request 쿼리 파라미터가 필요합니다."}, status=400)
        limit_param = request.query_params.get("limit", "3")
        try:
            limit = max(1, min(50, int(limit_param)))
        except (TypeError, ValueError):
            limit = 3
        qs = self.get_queryset().filter(analysis_request_id=ar_id).order_by("-score", "-id")[:limit]
        return Response(self.get_serializer(qs, many=True).data)

# Endpoints:
# GET    /api/v1/favorite-types
# POST   /api/v1/favorite-types
# GET    /api/v1/favorite-types/{id}
# PATCH  /api/v1/favorite-types/{id}
# DELETE /api/v1/favorite-types/{id}
class FavoriteTypeViewSet(BaseModelViewSet):
    queryset = FavoriteType.objects.select_related("user", "recommendation").all()
    serializer_class = FavoriteTypeSerializer
    filterset_fields = ["user", "recommendation"]
    search_fields = ["user__uuid", "recommendation__business_type__name"]
    ordering_fields = ["created_at", "id"]
    ordering = ["-created_at"]

# Endpoints:
# GET    /api/v1/favorite-spots
# POST   /api/v1/favorite-spots
# GET    /api/v1/favorite-spots/{id}
# PATCH  /api/v1/favorite-spots/{id}
# DELETE /api/v1/favorite-spots/{id}
class FavoriteSpotViewSet(BaseModelViewSet):
    queryset = FavoriteSpot.objects.select_related("user", "recommendation").all()
    serializer_class = FavoriteSpotSerializer
    filterset_fields = ["user", "recommendation"]
    search_fields = ["user__uuid", "recommendation__spot__address", "recommendation__business_type__name"]
    ordering_fields = ["created_at", "id"]
    ordering = ["-created_at"]

# Endpoints (추천 전용):
# GET /api/v1/recommendations/types/?lat=37.57&lon=126.98&radius_km=3&request_id=1   
class RecommendBusinessTypes(APIView):
    TARGET_TYPE_COUNT = 3

    def get(self, request):
        try:
            lat = float(request.query_params.get("lat"))
            lon = float(request.query_params.get("lon"))
        except Exception:
            return Response({"detail": "lat, lon 쿼리에 숫자로 넣어주세요."}, status=400)

        radius_km = _float_or_default(request.query_params.get("radius_km", 3.0), 3.0)
        radius_km = max(0.1, min(50.0, radius_km))
        req_id = request.query_params.get("request_id")

        # 후보 추출 (반경 내)
        lat_deg = radius_km / 111.0
        lon_deg = radius_km / (111.320 * max(0.0001, math.cos(math.radians(lat))))
        qs: QuerySet[Data] = Data.objects.filter(
            latitude__gte=lat - lat_deg, latitude__lte=lat + lat_deg,
            longitude__gte=lon - lon_deg, longitude__lte=lon + lon_deg,
        ).only(
            "id", "business_types", "address", "latitude", "longitude",
            "monthly_rent", "deposit", "daily_footfall_avg", "floor"
        )[:10]

        candidates = list(qs)
        if not candidates:
            return Response({"results": []})

        # 특징 계산
        enriched = []
        for c in candidates:
            enriched.append({
                "obj": c,
                "type": (c.business_types or "").strip() or "미분류",
                "distance_km": haversine_km(lat, lon, c.latitude, c.longitude),
                "foot": float(c.daily_footfall_avg or 0.0),
                "rent": float(c.monthly_rent or 0.0),
                "dep": float(c.deposit or 0.0),
                "floor": c.floor,
            })

        # 정규화 범위
        dmin, dmax = minmax([e["distance_km"] for e in enriched])
        fmin, fmax = minmax([e["foot"] for e in enriched])
        rmin, rmax = minmax([e["rent"] for e in enriched])
        pmin, pmax = minmax([e["dep"] for e in enriched])

        W_FOOT, W_DIST, W_RENT, W_DEP = 0.42, 0.25, 0.23, 0.10

        # 개별 점수
        items = []
        for e in enriched:
            foot_n = norm(e["foot"], fmin, fmax)
            dist_n = 1.0 - norm(e["distance_km"], dmin, dmax)
            rent_n = 1.0 - norm(e["rent"], rmin, rmax)
            dep_n = 1.0 - norm(e["dep"], pmin, pmax)
            floor_bonus = 0.03 if e["floor"] == 1 else (0.015 if e["floor"] in (2, 3) else 0.0)

            score = (W_FOOT*foot_n + W_DIST*dist_n + W_RENT*rent_n + W_DEP*dep_n) + floor_bonus
            items.append({"type": e["type"], "obj": e["obj"], "score": round(score * 5.0, 2), "distance_km": e["distance_km"]})

        # 업종별 그룹핑
        by_type: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for row in items:
            by_type[row["type"]].append(row)

        results = []
        for t, rows in by_type.items():
            rows.sort(key=lambda x: x["score"], reverse=True)
            topk = rows[:3]

            # 대표 매물 1개
            spot_dict = None
            if topk:
                o = topk[0]["obj"]
                spot_dict = {
                    "id": o.id,
                    "address": o.address,
                    "latitude": o.latitude,
                    "longitude": o.longitude,
                    "monthly_rent": o.monthly_rent,
                    "deposit": o.deposit,
                    "daily_footfall_avg": o.daily_footfall_avg,
                    "floor": o.floor,
                }

            why = safe_explain({
                "business_type": t,
                "distance_km": topk[0]["distance_km"] if topk else None,
                "daily_footfall_avg": _int_or_none(topk[0]["obj"].daily_footfall_avg) if topk else None,
                "monthly_rent": _int_or_none(topk[0]["obj"].monthly_rent) if topk else None,
                "deposit": _int_or_none(topk[0]["obj"].deposit) if topk else None,
                "floor": topk[0]["obj"].floor if topk else None,
            })

            avg_score = sum(r["score"] for r in topk) / max(1, len(topk))
            results.append({
                "business_type": t,
                "score": round(avg_score, 2),
                "count": len(rows),
                "spot": spot_dict,
                "why": why,
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        top = results[: self.TARGET_TYPE_COUNT]

        # DB 저장
        if req_id:
            try:
                req = AnalysisRequest.objects.get(id=req_id)
                with transaction.atomic():
                    for row in top:
                        bt, _ = BusinessType.objects.get_or_create(name=row["business_type"])
                        TypeRecommendation.objects.create(
                            analysis_request=req,
                            business_type=bt,
                            score=row["score"],
                            description=row["why"],
                            check_save=False,
                        )
            except AnalysisRequest.DoesNotExist:
                pass

        return Response({"results": top})


#   
# GET  /api/v1/recommendations/spots/?type=카페&request_id=1   
class RecommendSpotsByType(APIView):
    TARGET_COUNT = 3

    def get(self, request):
        qtype = (request.query_params.get("type") or request.query_params.get("business_type") or "").strip()
        if not qtype:
            return Response({"detail": "type(또는 business_type) 쿼리를 넣어주세요."}, status=400)

        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        lat = float(lat) if lat else None
        lon = float(lon) if lon else None

        radius_km = _float_or_default(request.query_params.get("radius_km", 5.0), 5.0)
        radius_km = max(0.1, min(50.0, radius_km))

        # save_flag = str(request.query_params.get("save", "")).lower() in ("1","true","yes")
        req_id = request.query_params.get("request_id")

        qs: QuerySet[Data] = Data.objects.filter(business_types__icontains=qtype)
        if lat is not None and lon is not None:
            lat_deg = radius_km / 111.0
            lon_deg = radius_km / (111.320 * max(0.0001, math.cos(math.radians(lat))))
            qs = qs.filter(
                latitude__gte=lat - lat_deg, latitude__lte=lat + lat_deg,
                longitude__gte=lon - lon_deg, longitude__lte=lon + lon_deg,
            )
        qs = qs.only("id","code","business_types","address","region","latitude","longitude",
                     "monthly_rent","deposit","daily_footfall_avg","floor")

        candidates = list(qs[:10000])
        if not candidates:
            return Response({"results": []})

        enriched = []
        for c in candidates:
            d_km = (haversine_km(lat, lon, c.latitude, c.longitude) if lat is not None and lon is not None else 0.0)
            foot = float(c.daily_footfall_avg or 0.0)
            enriched.append({
                "obj": c,
                "distance_km": d_km,
                "foot": foot,
                "rent": float(c.monthly_rent or 0.0),
                "dep":  float(c.deposit or 0.0),
                "floor": c.floor,
            })

        dmin, dmax = minmax([e["distance_km"] for e in enriched])
        fmin, fmax = minmax([e["foot"] for e in enriched])
        rmin, rmax = minmax([e["rent"] for e in enriched])
        pmin, pmax = minmax([e["dep"]  for e in enriched])

        if lat is not None and lon is not None:
            W_FOOT, W_DIST, W_RENT, W_DEP = 0.42, 0.23, 0.25, 0.10
        else:
            W_FOOT, W_RENT, W_DEP, W_DIST = 0.55, 0.30, 0.15, 0.0

        rows = []
        for e in enriched:
            foot_n = norm(e["foot"], fmin, fmax)
            rent_n = 1.0 - norm(e["rent"], rmin, rmax)
            dep_n  = 1.0 - norm(e["dep"],  pmin, pmax)
            dist_n = (1.0 - norm(e["distance_km"], dmin, dmax)) if W_DIST > 0 else 0.0

            floor_bonus = 0.0
            if isinstance(e["floor"], int):
                if e["floor"] == 1: floor_bonus = 0.03
                elif 2 <= e["floor"] <= 3: floor_bonus = 0.015

            score = (W_FOOT*foot_n + W_DIST*dist_n + W_RENT*rent_n + W_DEP*dep_n) + floor_bonus
            final_score = round(float(score) * 5.0, 2)   # ✅ 5점 만점 변환

            c = e["obj"]
            rows.append({
                "id": c.id,
                "code": c.code,
                "business_type": c.business_types,
                "address": c.address,
                "region": c.region,
                "latitude": c.latitude,
                "longitude": c.longitude,
                "monthly_rent": c.monthly_rent,
                "deposit": c.deposit,
                "daily_footfall_avg": c.daily_footfall_avg,
                "floor": c.floor,
                "distance_km": round(e["distance_km"], 3) if W_DIST > 0 else None,
                "score": final_score,
            })

        rows.sort(key=lambda x: x["score"], reverse=True)
        top = rows[: self.TARGET_COUNT]

        results = []
        for rec in top:
            why = safe_explain({
                "business_type": qtype or rec["business_type"],
                "distance_km": rec["distance_km"],
                "daily_footfall_avg": _int_or_none(rec["daily_footfall_avg"]),
                "monthly_rent": _int_or_none(rec["monthly_rent"]),
                "deposit": _int_or_none(rec["deposit"]),
                "floor": rec["floor"],
                "address": rec["address"],
            })
            rec_out = {**rec, "why": why}
            results.append(rec_out)

        if req_id:
            try:
                req = AnalysisRequest.objects.get(id=req_id)
                bt = BusinessType.objects.filter(name=qtype).first()
                if not bt:
                    bt = BusinessType.objects.create(name=qtype)

                with transaction.atomic():
                    for row in results:
                        SpotRecommendation.objects.create(
                            analysis_request=req,
                            spot_id=row["id"],
                            business_type=bt,
                            score=row["score"],
                            description=row["why"],
                            check_save=False,
                        )
            except AnalysisRequest.DoesNotExist:
                pass

        return Response({"results": results})
