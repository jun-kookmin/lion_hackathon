# api/models.py
import uuid as _uuid
from django.db import models
from django.utils.translation import gettext_lazy as _

def generate_uuid() -> str:
    return _uuid.uuid4().hex

class User(models.Model):
    uuid = models.CharField(_("방문자 UUID"), max_length=32, default=generate_uuid, editable=False)
    created_at = models.DateTimeField(_("생성 시각"), auto_now_add=True)

    def __str__(self):
        return f"User {self.uuid}"


class BusinessType(models.Model):
    name = models.CharField(_("업종명"), max_length=100)

    def __str__(self):
        return self.name


class Data(models.Model):
    code = models.CharField(_("상가업소번호"), max_length=50)
    business_code = models.CharField(_("분류코드"), max_length=100)
    business_types = models.CharField(_("분류명"), max_length=100)
    address = models.CharField(_("주소"), max_length=255)
    region_code = models.CharField(_("법정동코드"), max_length=100)
    region = models.CharField(_("법정동명"), max_length=100)
    floor = models.PositiveSmallIntegerField(_("층정보"), null=True)
    latitude = models.FloatField(_("위도"))
    longitude = models.FloatField(_("경도"))
    monthly_rent = models.PositiveIntegerField(_("월세(만원)"))
    deposit = models.PositiveIntegerField(_("보증금(만원)"), default=0)
    daily_footfall_avg = models.PositiveIntegerField(_("일평균 유동인구"), default=0)

    class Meta:
        ordering = ['id']
        verbose_name = _("후보 입지")
        verbose_name_plural = _("후보 입지 목록")

    def __str__(self):
        return f"{self.business_types} - {self.address} ({self.floor}층)"


class AnalysisRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="analysis_requests")
    business_type = models.ForeignKey(BusinessType, null=True, blank=True, on_delete=models.SET_NULL, related_name="analysis_requests")
    latitude = models.FloatField(_("입력 좌표(lon/lat)"), null=True, blank=True)
    longitude = models.FloatField(_("입력 좌표(lon/lat)"))
    address = models.CharField(_("입력 주소"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("요청 시각"), auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("분석 요청")
        verbose_name_plural = _("분석 요청 내역")



class TypeRecommendation(models.Model):
    analysis_request = models.ForeignKey(AnalysisRequest, on_delete=models.CASCADE, related_name="type_recommendations")
    business_type = models.ForeignKey(BusinessType, on_delete=models.CASCADE, related_name="type_recommendations")
    score = models.FloatField(_("추천 점수"))
    description = models.TextField(_("추천 사유"), blank=True, null=True)
    check_save = models.BooleanField(_("저장 여부"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score"]
        verbose_name = _("업종 추천 결과")
        verbose_name_plural = _("업종 추천 결과 목록")

    def __str__(self):
        return f"{self.business_type.name} ({self.score:.2f})"


class SpotRecommendation(models.Model):
    analysis_request = models.ForeignKey(AnalysisRequest, on_delete=models.CASCADE, related_name="spot_recommendations")
    spot = models.ForeignKey(Data, on_delete=models.CASCADE, related_name="spot_recommendations")
    business_type = models.ForeignKey(BusinessType, null=True, blank=True, on_delete=models.SET_NULL, related_name="spot_recommendations")
    score = models.FloatField(_("추천 점수"))
    description = models.TextField(_("추천 사유"), blank=True, null=True)
    check_save = models.BooleanField(_("저장 여부"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score"]
        verbose_name = _("위치 추천 결과")
        verbose_name_plural = _("위치 추천 결과 목록")

    def __str__(self):
        return f"{self.business_type.name if self.business_type else 'Unknown'} - {self.spot.address}"


class FavoriteType(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_type")
    recommendation = models.ForeignKey(TypeRecommendation, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("즐겨찾기 업종")
        verbose_name_plural = _("즐겨찾기 업종")

    def __str__(self):
        return f"{self.user.uuid} -> {self.recommendation.business_type.name}"


class FavoriteSpot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_spot")
    recommendation = models.ForeignKey(SpotRecommendation, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("즐겨찾기 위치")
        verbose_name_plural = _("즐겨찾기 위치")

    def __str__(self):
        return f"{self.user.uuid} -> {self.recommendation.spot.address}"
