from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.exceptions import MultipleObjectsReturned

from api.models import Data  # ← 앱명이 다르면 수정

# CSV 헤더 후보군 (이번에 확인된 헤더가 1순위로 들어있음)
CANDIDATES = {
    "uuid": ["상가업소번호", "점포번호", "매장ID"],
    "business_code": ["표준산업분류코드", "상권업종소분류코드", "업종소분류코드", "업종코드"],
    # 표준산업분류명이 있으면 우선 사용, 없으면 소분류명
    "business_types": ["표준산업분류명", "상권업종소분류명", "업종소분류명", "업종명"],
    "address_r": ["도로명주소", "주소도로명", "도로명"],
    "address_j": ["지번주소", "주소지번"],
    "region_code": ["법정동코드", "행정동코드", "시군구코드"],
    "region": ["법정동명", "행정동명", "시군구명"],
    "floor": ["층정보", "층", "층수"],
    "latitude": ["위도", "lat", "Latitude"],
    "longitude": ["경도", "lon", "Longitude"],
    "monthly_rent": ["월세(만원)", "월세_만원", "월세"],
    "deposit": ["보증금(만원)", "보증금_만원", "보증금"],
    "daily_footfall_avg": ["일평균 유동인구", "일평균_유동인구", "유동인구_일평균"],
}

def pick(cands: list[str], df_cols: list[str]) -> Optional[str]:
    for c in cands:
        if c in df_cols:
            return c
    return None

def to_int_safe(v, default=0) -> int:
    if pd.isna(v):
        return default
    try:
        if isinstance(v, str):
            s = v.strip().replace(",", "")
            if s == "":
                return default
            m = re.search(r"-?\d+", s)
            n = int(m.group()) if m else default
            return max(n, 0)  # 음수 방지 (PositiveIntegerField 호환)
        return max(int(float(v)), 0)
    except Exception:
        return default

def parse_floor_for_model(v) -> Optional[int]:
    """
    모델이 PositiveSmallIntegerField이므로 음수(지하)는 None으로 처리.
    '1층', '2F' → 1, 2 / 'B1', '지하1층' → None
    """
    if pd.isna(v):
        return None
    s = str(v).strip()
    if s == "":
        return None
    # 지하 표기 → None
    if "지하" in s or s.upper().startswith("B"):
        return None
    m = re.search(r"\d+", s.replace("층", "").replace("F", "").replace("f", ""))
    return int(m.group()) if m else None

class Command(BaseCommand):
    help = "상권 CSV를 Data 모델에 매핑해 적재합니다."

    def add_arguments(self, parser):
        parser.add_argument("--csv", required=True, help="CSV 파일 경로")
        parser.add_argument("--update", action="store_true",
                            help="기존 uuid가 있으면 값 갱신(update-or-create 유사)")
        parser.add_argument("--batch-size", type=int, default=1000,
                            help="bulk_create 배치 크기 (기본 1000)")

    def handle(self, *args, **opts):
        path = Path(opts["csv"])
        if not path.exists():
            raise CommandError(f"CSV 파일을 찾을 수 없습니다: {path}")

        # 인코딩 시도
        df = None
        for enc in ("utf-8", "utf-8-sig", "cp949"):
            try:
                df = pd.read_csv(path, encoding=enc)
                self.stdout.write(self.style.NOTICE(f"Read with encoding: {enc}"))
                break
            except Exception:
                continue
        if df is None:
            raise CommandError("CSV를 읽지 못했습니다. 인코딩을 확인하세요.")

        cols = list(df.columns)
        chosen = {k: pick(v, cols) for k, v in CANDIDATES.items()}
        address_col = chosen.get("address_r") or chosen.get("address_j")

        # 필수 컬럼 체크
        for r in ("uuid", "latitude", "longitude"):
            if not chosen.get(r):
                raise CommandError(f"필수 컬럼 매핑 실패: {r}. CSV 헤더 확인 필요. (후보: {CANDIDATES[r]})")

        self.stdout.write(self.style.SUCCESS("컬럼 매핑 결과:"))
        for k, v in chosen.items():
            self.stdout.write(f"  - {k}: {v}")

        created, updated = 0, 0
        to_create = []
        batch_size = int(opts["batch_size"])

        with transaction.atomic():
            if opts["update"]:
                # 안전한 갱신 모드 (중복 uuid도 방어)
                for _, row in df.iterrows():
                    uuid = str(row[chosen["uuid"]])

                    defaults = dict(
                        business_code=str(row[chosen["business_code"]]) if chosen["business_code"] else "",
                        business_types=str(row[chosen["business_types"]]) if chosen["business_types"] else "",
                        address=str(row[address_col]) if address_col else "",
                        region_code=str(row[chosen["region_code"]]) if chosen["region_code"] else "",
                        region=str(row[chosen["region"]]) if chosen["region"] else "",
                        floor=parse_floor_for_model(row[chosen["floor"]]) if chosen["floor"] else None,
                        latitude=float(row[chosen["latitude"]]),
                        longitude=float(row[chosen["longitude"]]),
                        monthly_rent=to_int_safe(row[chosen["monthly_rent"]]) if chosen["monthly_rent"] else 0,
                        deposit=to_int_safe(row[chosen["deposit"]]) if chosen["deposit"] else 0,
                        daily_footfall_avg=to_int_safe(row[chosen["daily_footfall_avg"]]) if chosen["daily_footfall_avg"] else 0,
                    )

                    try:
                        obj, is_created = Data.objects.get_or_create(uuid=uuid, defaults=defaults)
                        if not is_created:
                            for k, v in defaults.items():
                                setattr(obj, k, v)
                            obj.save(update_fields=list(defaults.keys()))
                            updated += 1
                        else:
                            created += 1
                    except MultipleObjectsReturned:
                        # uuid 중복 방어: 가장 먼저 찾은 레코드만 갱신하고 나머지는 무시
                        qs = Data.objects.filter(uuid=uuid).order_by("pk")
                        obj = qs.first()
                        for k, v in defaults.items():
                            setattr(obj, k, v)
                        obj.save(update_fields=list(defaults.keys()))
                        updated += 1
            else:
                # 신규만 빠르게 적재 (기존 uuid는 건너뛰기)
                existing = set(Data.objects.values_list("uuid", flat=True))
                for _, row in df.iterrows():
                    uuid = str(row[chosen["uuid"]])
                    if uuid in existing:
                        continue
                    obj = Data(
                        uuid=uuid,
                        business_code=str(row[chosen["business_code"]]) if chosen["business_code"] else "",
                        business_types=str(row[chosen["business_types"]]) if chosen["business_types"] else "",
                        address=str(row[address_col]) if address_col else "",
                        region_code=str(row[chosen["region_code"]]) if chosen["region_code"] else "",
                        region=str(row[chosen["region"]]) if chosen["region"] else "",
                        floor=parse_floor_for_model(row[chosen["floor"]]) if chosen["floor"] else None,
                        latitude=float(row[chosen["latitude"]]),
                        longitude=float(row[chosen["longitude"]]),
                        monthly_rent=to_int_safe(row[chosen["monthly_rent"]]) if chosen["monthly_rent"] else 0,
                        deposit=to_int_safe(row[chosen["deposit"]]) if chosen["deposit"] else 0,
                        daily_footfall_avg=to_int_safe(row[chosen["daily_footfall_avg"]]) if chosen["daily_footfall_avg"] else 0,
                    )
                    to_create.append(obj)
                    if len(to_create) >= batch_size:
                        Data.objects.bulk_create(to_create, batch_size=batch_size, ignore_conflicts=True)
                        created += len(to_create)
                        to_create.clear()
                if to_create:
                    Data.objects.bulk_create(to_create, batch_size=batch_size, ignore_conflicts=True)
                    created += len(to_create)

        self.stdout.write(self.style.SUCCESS(f"완료: created={created}, updated={updated}"))
