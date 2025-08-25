# 🦁 Lion Hackathon – 자리잡다 프로젝트

**자리잡다**는 예비 창업자와 소상공인을 위한 **위치 분석 & 추천 시스템**입니다.  
서울 등 도심에서 창업을 고민하는 사용자가 원하는 **업종, 예산, 이동 시간** 등을 입력하면,  
적합한 업종과 후보 위치를 선별하고 **지도 기반 UI**를 통해 한눈에 비교할 수 있도록 지원합니다.

본 프로젝트는 **2024년 라이온 해커톤(Lion Hackathon)**을 위해 제작되었으며,  
웹 클라이언트 · 서버 · 데이터베이스 · 모델/시드가 **하나의 저장소**에 포함되어 있습니다.

---

## ✨ 주요 기능

- **추천 업종 및 위치**  
  - 사용자가 선택한 예산·목적·출발지를 기반으로 업종(Type)과 후보 입지(Spot) 추천  
  - 하루 평균 유동인구, 월세·보증금, 층수, 업종 방문율 등을 활용하여 **추천 점수 산출**  
  - 추천 사유 및 지표를 함께 표시  

- **지도 기반 UI**  
  - **네이버맵 api** 활용  
  - 추천 위치를 지도에 마커로 표시  
  - 바텀시트 카드 ↔ 지도 간 **양방향 연동 UI** 제공  

- **층/필터 선택**  
  - B2/B1/1F/2F 층수 필터 적용 가능  

- **추천 사유 및 LLM 설명**  
  - `api/services/llm_openai.py` 모듈이 OpenAI API 호출  
  - 추천 사유, 예상 매출, 정부지원금, 운영 팁 등을 **자연어 설명**으로 생성  
  - 키가 없거나 API 호출 실패 시 **Fallback 함수 제공**  

- **데모 데이터 및 시드**  
  - `main/seed.py` 스크립트로 더미 사용자/업종/추천 결과 생성  
  - 초기 DB를 손쉽게 구축 가능  

- **REST API 제공**  
  - Django REST Framework 기반 CRUD API  
  - `/api/v1/type-recommendations/by_request` : 특정 요청에 대한 업종 추천  
  - `/api/v1/spot-recommendations/by_request` : 특정 요청에 대한 위치 추천  
  - `/api/v1/data/by_bbox` : 위도·경도 범위로 후보 데이터 필터링  

---

## 🛠 시스템 구성

### 1. 데이터 & 모델 (Django)
- `main/api/models.py`  
  - User, BusinessType, Data, AnalysisRequest, TypeRecommendation, SpotRecommendation, FavoriteType/FavoriteSpot  
  - **실제 상권 데이터 (상가번호, 주소, 층수, 보증금, 유동인구 등) 저장**

- `main/api/views.py`  
  - ModelViewSet 기반 CRUD API  
  - **추천 로직** 포함 (haversine 거리 계산, 점수 보정 함수 등)

- `main/api/services/llm_openai.py`  
  - OpenAI ChatGPT API 호출  
  - 최대 900자 이내, 5개 항목(추천 사유, 매출 예상, 성공 사례, 운영 팁, 정부 지원금) 제공  

---

### 2. 프론트엔드 (React + Vite)
- **구조** : `client/` 폴더, Vite 빌드 환경  
- **라우팅** : `wouter` 사용  
- **스타일링** : TailwindCSS + Radix UI  
- **기능** : 지도/바텀시트/추천 카드 컴포넌트 구현  

---

### 3. 서버 (Express / Vite)
- `server/index.ts`  
- Express 서버에서 API 라우트 등록 후, Vite 미들웨어로 React 앱 제공  
- 개발 모드: HMR 지원  
- 빌드 모드: 정적 파일(`dist/`) 서빙  

---

## ⚡ 설치 및 실행 방법

### 요구 사항
- Node.js ≥ 18.x  
- Python ≥ 3.10  
- npm 또는 pnpm  
- OpenAI API Key  

### 실행 절차

1. 저장소 클론
   ```bash
   git clone https://github.com/jun-kookmin/lion_hackathon.git
   cd lion_hackathon

프론트엔드/서버 의존성 설치

npm install


백엔드 의존성 설치 (가상환경 권장)

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


환경 변수 설정 (.env)

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=postgres://user:pass@localhost:5432/lion


DB 마이그레이션 & 시드

python manage.py migrate
python main/seed.py


애플리케이션 실행

Django 서버 (포트 8000)

python manage.py runserver


프론트엔드/Express 서버 (포트 5000)

npm run dev


빌드 & 배포

npm run build
npm start
