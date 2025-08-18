import os
import django
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
django.setup()

from api.models import (
    User, BusinessType, AnalysisRequest,
    TypeRecommendation, SpotRecommendation,
    FavoriteType, FavoriteSpot, Data
)


def run():
    print("더미데이터 생성 시작...")

    # User 생성
    users = [User.objects.create() for _ in range(5)]

    # BusinessType 생성
    bt_names = ["카페", "식당", "헬스장", "편의점", "학원"]
    business_types = [BusinessType.objects.create(name=name) for name in bt_names]

    # AnalysisRequest 생성
    analysis_requests = []
    for u in users:
        for _ in range(2):
            ar = AnalysisRequest.objects.create(
                user=u,
                business_type=random.choice(business_types),
                plan=random.choice(["A", "B"]),
                latitude=37.5 + random.random(),
                longitude=127.0 + random.random(),
                address=f"서울시 어딘가 {random.randint(1, 100)}번지"
            )
            analysis_requests.append(ar)

    # TypeRecommendation 생성
    type_recs = []
    for ar in analysis_requests:
        for bt in random.sample(business_types, 3):
            tr = TypeRecommendation.objects.create(
                analysis_request=ar,
                business_type=bt,
                score=round(random.uniform(0, 100), 2),
                description=f"{bt.name} 추천 이유",
                check_save=random.choice([True, False])
            )
            type_recs.append(tr)

    # SpotRecommendation 생성 (기존 Data 활용)
    data_all = list(Data.objects.all())   # ✅ Data 테이블에서 가져오기
    spot_recs = []
    for ar in analysis_requests:
        for bt in random.sample(business_types, 2):
            sr = SpotRecommendation.objects.create(
                analysis_request=ar,
                spot=random.choice(data_all),   # ✅ 랜덤 Data 연결
                business_type=bt,
                score=round(random.uniform(0, 100), 2),
                description=f"{bt.name} 위치 추천 이유",
                check_save=random.choice([True, False])
            )
            spot_recs.append(sr)

    # FavoriteType 생성
    for u in users:
        for tr in random.sample(type_recs, 2):
            FavoriteType.objects.create(
                user=u,
                recommendation=tr
            )

    # FavoriteSpot 생성
    for u in users:
        for sr in random.sample(spot_recs, 2):
            FavoriteSpot.objects.create(
                user=u,
                recommendation=sr
            )

    print("더미데이터 생성 완료 ✅")


if __name__ == "__main__":
    run()
