from __future__ import annotations
import random
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.utils import timezone

from api import models


class Command(BaseCommand):
    help = "Demo data seeding for BusinessType/Tag/Data/AnalysisRequest/Recommendation/Favorite"

    def add_arguments(self, parser):
        parser.add_argument("--spots", type=int, default=30, help="생성할 입지 개수")
        parser.add_argument("--recs", type=int, default=20, help="생성할 추천 개수")

    def handle(self, *args, **opts):
        spots = int(opts["spots"])
        recs = int(opts["recs"])

        # User
        user = models.User.objects.order_by("created_at").first()
        if not user:
            user = models.User.objects.create()

        # Business Types
        root_bt, _ = models.BusinessType.objects.get_or_create(name="음식점", parent=None)
        cafe, _ = models.BusinessType.objects.get_or_create(name="카페", parent=root_bt)
        chicken, _ = models.BusinessType.objects.get_or_create(name="치킨", parent=root_bt)
        kfood, _ = models.BusinessType.objects.get_or_create(name="한식", parent=root_bt)
        bts = [cafe, chicken, kfood]

        # Tags
        tag_names = ["역세권", "오피스밀집", "주거밀집", "학원가", "관광지", "공원인접", "대형마트인접"]
        tag_objs = []
        for n in tag_names:
            t, _ = models.Tag.objects.get_or_create(name=n)
            tag_objs.append(t)

        # Data (candidate spots) around Seoul bbox
        def rand_point():
            lng = random.uniform(126.90, 127.15)
            lat = random.uniform(37.45, 37.70)
            return Point(lng, lat, srid=4326)

        for i in range(spots):
            d = models.Data.objects.create(
                point=rand_point(),
                address=f"서울시 어딘가 {i+1}번지",
                region=random.choice(["강남구", "종로구", "마포구", "송파구", "광진구"]),
                monthly_rent=random.choice([80, 120, 150, 200, 250, 300]),
                deposit=random.choice([500, 1000, 2000, 3000]),
                daily_footfall_avg=random.randint(1000, 20000),
            )
            d.allow_business_types.set(random.sample(bts, k=random.randint(1, len(bts))))
            d.tags.set(random.sample(tag_objs, k=random.randint(1, min(3, len(tag_objs)))))

        # Analysis Requests
        ar = models.AnalysisRequest.objects.create(
            user=user,
            business_type=random.choice(bts),
            plan=random.choice(["A", "B"]),
            point=rand_point(),
            address="서울특별시 중구 세종대로 110",
        )

        # Recommendations
        data_ids = list(models.Data.objects.values_list("id", flat=True))
        for _ in range(recs):
            d_id = random.choice(data_ids)
            d = models.Data.objects.get(id=d_id)
            r = models.Recommendation.objects.create(
                analysis_request=ar,
                spot=d,
                business_type=random.choice(bts),
                score=round(random.uniform(0.4, 0.98), 3),
                description="유동인구/임대료/태그 기반 가중치 임시 점수",
            )
            # link tags via through model
            for t in random.sample(tag_objs, k=random.randint(1, 3)):
                models.RecommendationTag.objects.get_or_create(recommendation=r, tag=t)

        # Favorite (top 3)
        top_recs = models.Recommendation.objects.order_by("-score")[:3]
        for r in top_recs:
            models.Favorite.objects.get_or_create(user=user, recommendation=r)

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
