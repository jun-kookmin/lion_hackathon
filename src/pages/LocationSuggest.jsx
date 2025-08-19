//위치 추천
import React, { useMemo, useRef, useState, useEffect } from "react";
import "./LocationSuggest.css";

const cardData = [
  { label: "레코드카페", color: "#FF00A8" },
  { label: "헤나카페",   color: "#FF6B00" },
  { label: "실내보드",   color: "#A020F0" },
  { label: "캠핑 바",     color: "#FF00A8" }, // 초기 중앙
  { label: "헬스장",     color: "#FF6B00" },
  { label: "복싱클럽",   color: "#A020F0" },
  { label: "VR FPS",     color: "#7ED957" },
];

const COLOR_NAME = {
  pink:   "#FF00A8",
  orange: "#FF6B00",
  purple: "#A020F0",
  green:  "#7ED957", 
};

// 버튼에 표시할 한글 라벨
const NAME_KR = {
  all:    "전체",
  pink:   "카페 / 음식",
  orange: "카페 / 음식",
  purple: "취미 / 문화",
  green:  "키즈 / 반려",
};

const mod = (i, n) => (i % n + n) % n;

export default function LocationSuggest() {
  const initial = useMemo(
    () => Math.max(0, cardData.findIndex(c => c.label === "캠핑 바")),
    []
  );
  const [current, setCurrent] = useState(initial);

  // 스와이프 제스처 (왼쪽 스와이프 = prev, 오른쪽 스와이프 = next)
  const startX = useRef(null);
  const deltaX = useRef(0);
  const dragging = useRef(false);

  const handleStart = (x) => { startX.current = x; deltaX.current = 0; dragging.current = true; };
  const handleMove  = (x) => { if (!dragging.current) return; deltaX.current = x - startX.current; };
  const handleEnd   = () => {
    if (!dragging.current) return;
    const threshold = 40;
    if (deltaX.current <= -threshold) prev(); // 왼쪽으로 넘기면 이전 카드
    else if (deltaX.current >= threshold) next(); // 오른쪽으로 넘기면 다음 카드
    startX.current = null; deltaX.current = 0; dragging.current = false;
  };

  const prev = () => setCurrent(c => mod(c - 1, cardData.length));
  const next = () => setCurrent(c => mod(c + 1, cardData.length));

  const leftIdx  = mod(current - 1, cardData.length);
  const rightIdx = mod(current + 1, cardData.length);

  return (
    <div className="location-container">
      <div className="location-topbar">
        <span className="tab active">어디가 좋을까?</span>
        <span className="tab">여기에 뭐할까?</span>
        <span className="click-icon">✳️</span>
      </div>

      <div className="location-body">
        <p className="prompt">매장 콘셉트를 골라주세요!</p>
        <button className="category-button">전체 ▾</button>

        {/* === 가운데 정렬 캐러셀(모든 카드 동일 크기) === */}
        <div
          className="carousel"
          onMouseDown={(e) => handleStart(e.clientX)}
          onMouseMove={(e) => dragging.current && handleMove(e.clientX)}
          onMouseUp={handleEnd}
          onMouseLeave={handleEnd}
          onTouchStart={(e) => handleStart(e.touches[0].clientX)}
          onTouchMove={(e) => handleMove(e.touches[0].clientX)}
          onTouchEnd={handleEnd}
        >
          {/* 왼쪽 카드 */}
          <div
            className="card left"
            style={{ background: cardData[leftIdx].color }}
            onClick={prev}
          >
            <div className="card-glyph"></div>
          </div>

          {/* 중앙 카드 (크기 동일, 중앙 정렬만) */}
          <div className="card center" style={{ background: cardData[current].color }}>
            <div className="card-glyph"></div>
          </div>
          <div className="card-label">{cardData[current].label}</div>

          {/* 오른쪽 카드 */}
          <div
            className="card right"
            style={{ background: cardData[rightIdx].color }}
            onClick={next}
          >
            <div className="card-glyph"></div>
          </div>

          {/* 선택: 화살표 버튼 */}
          <button className="nav prev" onClick={prev} aria-label="이전">‹</button>
          <button className="nav next" onClick={next} aria-label="다음">›</button>
        </div>

        <div className="search-bar">
          <input type="text" placeholder="고기 커스텀 국밥집" />
          <button className="search-button" aria-label="검색"></button>
        </div>
      </div>

      <div className="bottom-tabbar">
        <span>🏠</span>
        <span>🏪</span>
        <span>🏢</span>
        <span>💬</span>
        <span>👤</span>
      </div>
    </div>
  );
}
