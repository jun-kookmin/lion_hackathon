//첫 화면
// Home.jsx
import React from "react";
import { useNavigate } from "react-router-dom"; // 🔹 추가
import "./Home.css";

const reviews = [
  "자리잡다의 새로운 모습을 알게 되었고, 지역의 변화를 실감했어요!",
  "AI 추천이 정확해서 신뢰가 생겨요.",
  "너무 편하고 좋은 것 같아요",
  "디자인이 깔끔하고 보기 편해요.",
  "서비스 속도가 빨라서 좋아요!"
];

const Home = () => {
  const navigate = useNavigate(); 

  const handleLoginClick = () => {
    navigate("/locationsuggest"); 
  };

  return (
    <div className="home-container">
      <header className="header">
        <p className="subtitle">AI 추천 상권과 창업 아이템은</p>
        <h1 className="logo">자리잡다</h1>
        {/* <button className="outline-button">알아보기</button> */}
      </header>

      <section className="review-section">
        <h2 className="section-title">솔직후기</h2>
        <div className="review-scroll">
          {reviews.map((text, index) => (
            <div key={index} className="review-card">
              <p className="review-title">창업하는 오소리</p>
              <p className="review-text">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="cta-section">
        <button className="primary-button" onClick={handleLoginClick}>
          간편 로그인하고 픽업하기
        </button>
        <p className="sub-link">회원이 아니신가요? 회원가입하기</p>
      </section>
    </div>
  );
};

export default Home;
