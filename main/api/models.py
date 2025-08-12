import uuid as _uuid
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils.translation import gettext_lazy as _

def generate_uuid() -> str:
    return _uuid.uuid4().hex

class User(models.Model):
    uuid = models.CharField(
        _("방문자 UUID"),
        primary_key=True,
        max_length=32,
        default=generate_uuid,
        editable=False, 
        )
    
    created_at = models.DateTimeField(
        _("생성 시각"), 
        auto_now_add=True
        )

class BusinessType(models.Model):
    name = models.CharField(
        _("업종명"), 
        max_length=100, 
        )
    
    parent = models.ForeignKey(
        "self", 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name="children"
        )


    
class Tag(models.Model):
    name = models.CharField(
        _("태그명"), 
        max_length=100, 
        )



class Data(models.Model):
    point = gis_models.PointField(_("좌표(lon/lat)"), geography=True) # 위도 경도
    address = models.CharField(_("주소"), max_length=255) # 도로명 주소 
    region = models.CharField(_("지역명"), max_length=100, blank=True) # 법정동명

    allow_business_types = models.ManyToManyField(
        BusinessType,
        blank=True,                    
        related_name="candidate_spots",
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,                 
        related_name="candidate_spots",
    )

    monthly_rent = models.PositiveIntegerField(_("월세(만원)"))
    deposit = models.PositiveIntegerField(_("보증금(만원)"), default=0)
    daily_footfall_avg = models.PositiveIntegerField(_("일평균 유동인구"), default=0)

    class Meta:
        indexes = [
            gis_models.Index(fields=["point"]),
            models.Index(fields=["monthly_rent"]),
        ]
        verbose_name = _("후보 입지")
        verbose_name_plural = _("후보 입지 목록")


class AnalysisRequest(models.Model):
    PLAN_CHOICES = [
        ("A", "Plan A"),
        ("B", "Plan B"),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="analysis_requests"
        )
    # 업종 -> 소분류? 대분류 고민해야함
    business_type = models.ForeignKey(
        BusinessType, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name="analysis_requests"
        )
    # 플랜
    plan = models.CharField(
        _("플랜"), 
        max_length=1, 
        choices=PLAN_CHOICES
        )
    # 위도 경도 
    point = gis_models.PointField(
        _("입력 좌표(lon/lat)"), 
        geography=True, 
        null=True, 
        blank=True
        )
    # 도로명
    address = models.CharField(
        _("입력 주소"), 
        max_length=255, 
        null=True,
        blank=True
        )
    
    created_at = models.DateTimeField(
        _("요청 시각"), 
        auto_now_add=True
        )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("분석 요청")
        verbose_name_plural = _("분석 요청 내역")

  
    


class Photo(models.Model):
    analysis_request = models.ForeignKey(
        AnalysisRequest, 
        on_delete=models.CASCADE, 
        related_name="photos"
        )
    
    image = models.ImageField(
        _("이미지"), 
        upload_to="analysis_photos/%Y/%m/%d"
        )
    
    uploaded_at = models.DateTimeField(
        auto_now_add=True
        )


class Recommendation(models.Model):
    analysis_request = models.ForeignKey(
        AnalysisRequest,
        on_delete=models.CASCADE, 
        related_name="recommendations"
        )
    
    spot = models.ForeignKey(
        Data, 
        on_delete=models.CASCADE, 
        related_name="recommendations"
        )
    
    business_type = models.ForeignKey(
        BusinessType,
        on_delete=models.CASCADE,
        related_name="recommendations"
        )

    score = models.FloatField(
        _("추천 점수")
        )
    
    description = models.TextField(
        _("추천 사유"),
        )
    
    created_at = models.DateTimeField(
        auto_now_add=True
        )

    class Meta:
        ordering = ["-score"]
        verbose_name = _("추천 결과")
        verbose_name_plural = _("추천 결과 목록")


class RecommendationTag(models.Model):
    recommendation = models.ForeignKey(
        Recommendation, 
        on_delete=models.CASCADE
        )
    
    tag = models.ForeignKey(
        Tag, 
        on_delete=models.CASCADE
        )

    class Meta:
        unique_together = ("recommendation", "tag")
        verbose_name = _("추천-태그 연결")
        verbose_name_plural = _("추천-태그 연결 목록")


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    recommendation = models.ForeignKey(
        Recommendation, on_delete=models.CASCADE, related_name="favorites"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("즐겨찾기")
        verbose_name_plural = _("즐겨찾기 목록")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recommendation"],
                name="uniq_favorite_user_recommendation",
            )
        ]