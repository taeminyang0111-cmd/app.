# app.py
import os
import re
from datetime import datetime, timedelta

import requests
import pandas as pd
import streamlit as st


# =============================
# Page config
# =============================
st.set_page_config(
    page_title="AI 습관 트래커",
    page_icon="📊",
    layout="wide",
)


# =============================
# Sidebar: API Keys
# =============================
st.sidebar.header("🔑 API 설정")

owm_key = st.sidebar.text_input(
    "OpenWeatherMap API Key",
    value=os.getenv("OPENWEATHERMAP_API_KEY", ""),
    type="password",
)

st.sidebar.caption("※ OpenAI 없이도 모든 기능 체험 가능")


# =============================
# API Functions
# =============================
@st.cache_data(ttl=600)
def get_weather(city: str, api_key: str):
    if not api_key:
        return None
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",
            "lang": "kr",
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        return {
            "city": city,
            "description": data["weather"][0]["description"],
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
        }
    except Exception:
        return None


@st.cache_data(ttl=600)
def get_dog_image():
    try:
        r = requests.get("https://dog.ceo/api/breeds/image/random", timeout=10)
        data = r.json()
        url = data.get("message")
        breed = "unknown"
        m = re.search(r"/breeds/([^/]+)/", url)
        if m:
            breed = m.group(1).replace("-", " ")
        return {"url": url, "breed": breed}
    except Exception:
        return None


# =============================
# 🌦️ Weather × Habit Synergy
# =============================
def weather_habit_synergy(weather: dict | None):
    if not weather:
        return "🌱 날씨 정보 없음 → 오늘은 핵심 습관 1~2개만 해도 충분해요."

    desc = weather["description"]
    temp = weather["temp"]

    if any(x in desc for x in ["비", "눈"]):
        return "☔ 비 오는 날! **실내 스트레칭 + 독서** 조합 추천"
    if temp >= 30:
        return "🔥 더운 날씨! **물 마시기 + 휴식**이 오늘의 핵심"
    if temp <= 0:
        return "❄️ 추운 날씨! **수면 관리 + 가벼운 스트레칭**"
    if "맑" in desc:
        return "☀️ 맑은 날씨! **산책 겸 운동 미션** 도전하기 좋아요"

    return "🌤️ 무난한 날씨! 컨디션에 맞춰 균형 있게 가요"


# =============================
# 🏅 Streak & Badge System
# =============================
def calculate_streak(history):
    streak = 0
    for day in reversed(history):
        if day["rate"] >= 60:
            streak += 1
        else:
            break
    return streak


def streak_badge(streak: int):
    if streak >= 21:
        return "🏆 습관 마스터", "21일 연속! 습관이 정체성이 됐어요."
    if streak >= 7:
        return "🔥 7일 스트릭", "일주일 연속 성공! 흐름 완성!"
    if streak >= 3:
        return "✨ 3일 스타터", "좋은 출발이에요. 이 리듬 유지!"
    return None, None


# =============================
# 🐶 오늘의 동료 캐릭터
# =============================
DOG_PERSONA = {
    "retriever": ("긍정왕", "작은 성공도 크게 칭찬해주는 스타일"),
    "shepherd": ("집중력 장인", "한 가지 목표를 끝까지 파는 타입"),
    "bulldog": ("끈기의 상징", "느려도 절대 포기하지 않음"),
    "poodle": ("두뇌파", "계획 세우기와 루틴에 강함"),
    "shiba": ("독립 전사", "스스로 정한 규칙은 꼭 지킴"),
    "husky": ("에너지 폭발", "움직이면 컨디션이 살아남"),
}


def dog_companion_message(breed: str):
    for key, (title, desc) in DOG_PERSONA.items():
        if key in breed.lower():
            return title, desc
    return "오늘의 동료", "오늘 하루 끝까지 함께 가주는 친구"


# =============================
# Session State (7일)
# =============================
if "history" not in st.session_state:
    today = datetime.now().date()
    demo_rates = [40, 60, 80, 20, 100, 60]
    st.session_state.history = [
        {
            "date": (today - timedelta(days=i)).strftime("%Y-%m-%d"),
            "rate": r,
        }
        for i, r in zip(range(6, 0, -1), demo_rates)
    ] + [{"date": today.strftime("%Y-%m-%d"), "rate": 0}]


# =============================
# Main UI
# =============================
st.title("📊 AI 습관 트래커")
st.caption("날씨·연속성·동료 캐릭터로 습관을 게임처럼")

# --- Habit Check
st.subheader("✅ 오늘의 습관 체크인")

habits = [
    ("🌅", "기상 미션"),
    ("💧", "물 마시기"),
    ("📚", "공부/독서"),
    ("🏃", "운동하기"),
    ("😴", "수면"),
]

col1, col2 = st.columns(2)
checked = []

with col1:
    for emoji, h in habits[:3]:
        if st.checkbox(f"{emoji} {h}"):
            checked.append(h)

with col2:
    for emoji, h in habits[3:]:
        if st.checkbox(f"{emoji} {h}"):
            checked.append(h)

mood = st.slider("🙂 오늘 기분 점수", 1, 10, 7)

cities = [
    "Seoul", "Busan", "Incheon", "Daegu", "Daejeon",
    "Gwangju", "Ulsan", "Suwon", "Seongnam", "Jeju",
]
city = st.selectbox("📍 도시 선택", cities)

# --- Weather Hint
weather = get_weather(city, owm_key)
st.info(weather_habit_synergy(weather))

# --- Metrics
completed = len(checked)
rate = int(completed / 5 * 100)

m1, m2, m3 = st.columns(3)
m1.metric("달성률", f"{rate}%")
m2.metric("완료 습관", f"{completed}/5")
m3.metric("기분", f"{mood}/10")

# --- Save today
today_str = datetime.now().strftime("%Y-%m-%d")
st.session_state.history[-1] = {"date": today_str, "rate": rate}

# --- Streak & Badge
streak = calculate_streak(st.session_state.history)
badge, badge_msg = streak_badge(streak)

st.subheader("🏅 연속 달성")
st.write(f"🔥 현재 **{streak}일 연속 달성 중**")

if badge:
    st.success(f"{badge}\n\n{badge_msg}")
else:
    st.info("다음 배지까지 한 걸음 남았어요 🙂")

# --- Chart
st.subheader("📈 최근 7일 달성률")
df = pd.DataFrame(st.session_state.history).set_index("date")
st.bar_chart(df)

# --- Dog Companion
dog = get_dog_image()
if dog:
    title, desc = dog_companion_message(dog["breed"])

    st.subheader("🐶 오늘의 동료")
    c1, c2 = st.columns([1, 2])

    with c1:
        st.image(dog["url"], use_container_width=True)

    with c2:
        st.markdown(f"### {title}")
        st.write(f"**품종**: {dog['breed']}")
        st.write(f"**성격**: {desc}")
        st.success("오늘 하루, 이 친구와 끝까지 가봅시다!")

# --- Footer
with st.expander("ℹ️ 이 앱에서 배울 수 있는 것"):
    st.markdown("""
- 🌦️ 외부 API를 **행동 결정 요소**로 활용하는 법  
- 🏅 상태 기반 로직으로 **동기부여 시스템** 설계  
- 🐶 캐릭터화로 UX 몰입도 높이기  
- 📊 session_state로 사용자 기록 관리
""")
