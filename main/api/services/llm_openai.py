from __future__ import annotations
import os, json
from openai import OpenAI

def int_or_none(v):
    try:
        return int(v)
    except Exception:
        return None

client = OpenAI() 
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_KO = (
    "너는 입지 추천 사유를 작성하는 도우미다. "
    "유동인구는 '보행량'이며 실제 방문자가 아님을 명시하라. "
    "features에 'assumed_visit_rate'와 'estimated_visitors'가 있으면 이를 사용해, "
    "전환율 r% 가정 시 방문자 추정 N명을 사실대로 설명하라. "
    "과장/추정치 임의 생성 금지, 주어진 값만 사용."
)

def _fallback(f: dict) -> str:
    parts = []
    if f.get("distance_km") is not None:
        parts.append(f"위치 {f['distance_km']:.1f}km")
    if f.get("monthly_rent") is not None:
        parts.append(f"임대료 {f['monthly_rent']:,}원")
    if f.get("deposit") is not None:
        parts.append(f"보증금 {f['deposit']:,}원")
    if f.get("daily_footfall_avg") is not None:
        parts.append(f"일 유동인구 {f['daily_footfall_avg']:,}명")

    vr = f.get("assumed_visit_rate")
    ev = int_or_none(f.get("estimated_visitors"))
    if vr is not None and ev is not None:
        parts.append(f"(유동인구는 보행량이며, 전환율 {vr*100:.1f}% 가정 시 방문자 {ev:,}명 추정)")

    base = ", ".join(parts) if parts else "여러 지표가 균형적"
    return base + " 등을 종합해 상위 후보로 선정했습니다."

def explain(features: dict, lang: str = "ko") -> str:
    try:
        prompt = f"""
다음 JSON 지표만 근거로 아래 형식을 그대로 작성하라.
규칙:
- 각 항목은 정확히 2문장
- 과장 및 임의 추정/계산(예: 매출, 순이익) 금지. 주어진 수치만 언급
- 데이터가 없으면 '데이터 없음'이라고 적기
- 전체는 800자 이내

형식:
1. 추천 사유
2. 예상 매출 수익 사유
3. 유사 성공 사례   
4. 창업 운영 팁
5. 정부 지원금 정보

JSON:
{json.dumps(features, ensure_ascii=False)}
""".strip()

        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_KO},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.2,
            max_tokens=200,   
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return _fallback(features)
