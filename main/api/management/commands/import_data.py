from __future__ import annotations
import csv, re
from typing import Any, Dict, List, Optional
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from api.models import Data

NUM_RE = re.compile(r"-?\d+")

#python manage.py import_data --path "C:\Users\rudwn\Desktop\hackaton\csv\상권정보.csv" --encoding utf-8-sig --fres

def pick(d: Dict[str, Any], *keys: str) -> str:
    for k in keys:
        if k in d and str(d[k]).strip() != "":
            return str(d[k]).strip()
    return ""

def to_int(s: str, default: int = 0) -> int:
    if not s:
        return default
    s = s.replace(",", "").strip()
    m = NUM_RE.search(s)
    if not m:
        return default
    try:
        return int(m.group())
    except Exception:
        return default

def to_floor(s: str) -> Optional[int]:
    if not s:
        return None
    n = to_int(s, default=0)
    if n <= 0:
        return None
    return n

def to_float(s: str) -> Optional[float]:
    if not s:
        return None
    try:
        return float(s.replace(",", "").strip())
    except Exception:
        return None

class Command(BaseCommand):
    help = "상권 CSV를 Data 모델로 적재 (여분 컬럼은 무시)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--path", required=True, help="CSV 파일 경로 (예: 상권정보.csv)")
        parser.add_argument("--encoding", default="cp949", help="파일 인코딩 (기본 cp949)")
        parser.add_argument("--fresh", action="store_true", help="적재 전 Data 테이블 비우기")
        parser.add_argument("--delimiter", default=",", help="CSV 구분자 (기본 ,)")

    def handle(self, *args, **opts):
        path: str = opts["path"]
        encoding: str = opts["encoding"]
        delimiter: str = opts["delimiter"]
        fresh: bool = opts["fresh"]

        # 필요하면 테이블 초기화
        if fresh:
            Data.objects.all().delete()

        with open(path, "r", encoding=encoding, newline="") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            rows = list(reader)

        # 중복 code(상가업소번호) 방지: 마지막 레코드 우선
        uniq: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            code = pick(r, "상가업소번호")
            if not code:
                continue
            uniq[code] = r

        objs: List[Data] = []
        for r in uniq.values():
            code = pick(r, "상가업소번호")

            # 업종 코드/명: 소분류 우선
            business_code = pick(
                r,
                "상권업종소분류코드",
                "상권업종중분류코드",
                "상권업종대분류코드",
                "표준산업분류코드",
            )
            business_types = pick(
                r,
                "상권업종소분류명",
                "상권업종중분류명",
                "상권업종대분류명",
                "표준산업분류명",
            )

            address = pick(r, "도로명주소", "지번주소")
            region_code = pick(r, "법정동코드")   # 없으면 빈 문자열로 저장됨
            region = pick(r, "법정동명")
            floor = to_floor(pick(r, "층정보"))
            lon = to_float(pick(r, "경도"))
            lat = to_float(pick(r, "위도"))

            # 금액/유동인구: 엑셀 값 그대로(단위 변환 없음)
            deposit = to_int(pick(r, "예상보증금", "보증금(만원)"), default=0)
            monthly_rent = to_int(pick(r, "예상월세", "월세(만원)"), default=0)
            daily_footfall_avg = to_int(pick(r, "예상유동인구", "일평균 유동인구"), default=0)

            # 필수: code, 위경도
            if not code or lat is None or lon is None:
                continue

            objs.append(
                Data(
                    code=code,
                    business_code=business_code,
                    business_types=business_types,
                    address=address,
                    region_code=region_code,
                    region=region,
                    floor=floor,
                    latitude=lat,
                    longitude=lon,
                    monthly_rent=monthly_rent,
                    deposit=deposit,
                    daily_footfall_avg=daily_footfall_avg,
                )
            )

        with transaction.atomic():
            Data.objects.bulk_create(objs, batch_size=2000)

        self.stdout.write(self.style.SUCCESS(f"Imported: {len(objs)} rows"))
