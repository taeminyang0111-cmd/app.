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

st.sidebar.caption("※ OpenAI 없이도 날씨·배지 기능은 동작합니다")


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
        return "🌱 날씨 정보 없음 → 오늘은 핵심 습관 1~2개만 지켜도 충분해요."

    desc = weather["description"]
    temp = weather["temp"]

    if any(x in desc for x in ["비", "눈"]):
        return "☔ 비 오는 날! **실내 스트레칭 + 독서** 조합을 추천해요."
    if temp >= 30:
        return "🔥 더운 날씨! **물 마시기 + 휴식**을 최우선 미션으로!"
    if temp <= 0:
        return "❄️ 추운 날씨! **수면 관리 + 가벼운 스트레칭**으로 체력 보존!"
    if "맑" in desc:
        return "☀️ 맑은 날씨! **산책 겸 운동 미션** 도전하기 딱 좋아요."

    return "🌤️ 무난한 날씨! 오늘 컨디션에 맞춰 균형 있게 가요."


# =============================
# 🏅 Streak & Badge System
# =============================
def calculate_streak(history):
    """연속으로 달성률 60% 이상인 일수"""
    streak = 0
    for day in reversed(history):
        if day["rate"] >= 60:
            streak += 1
        else:
            break
    return streak


def streak_badge(streak: int):
    if streak >= 21:
        return "🏆 습관 마스터", "21일 연속 달성! 이제 습관이 정체성이에요."
    if streak >= 7:
        return "🔥 7일 스트릭", "일주일 연속 성공! 흐름이 완성됐어요."
    if streak >= 3:
        return "✨ 3일 스타터", "좋은 출발이에요. 이 리듬 유지!"
    return None, None


# =============================
# Session State (7일 기록)
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
st.caption("날씨와 연속성을 고려해 오늘의 습관을 설계해요")

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

st.subheader("🏅 연속 달성 현황")
st.write(f"🔥 현재 스트릭: **{streak}일 연속**")

if badge:
    st.success(f"{badge} 획득!\n\n{badge_msg}")
else:
    st.info("다음 배지까지 조금만 더 가볼까요? 🙂")

# --- Chart
st.subheader("📈 최근 7일 달성률")
df = pd.DataFrame(st.session_state.history).set_index("date")
st.bar_chart(df)

# --- Dog
dog = get_dog_image()
if dog:
    st.subheader("🐶 오늘의 동료")
    st.image(dog["url"], use_container_width=True)
    st.caption(f"품종: {dog['breed']}")

# --- Footer
with st.expander("ℹ️ 기능 안내"):
    st.markdown("""
- 🌦️ **날씨 시너지**: 날씨에 따라 오늘의 추천 습관 전략이 달라집니다  
- 🏅 **스트릭 & 배지**: 달성률 60% 이상이면 연속 기록 인정  
- 🐶 **오늘의 동료**: 매일 다른 강아지가 함께합니다  
- 📊 **7일 차트**: 최근 습관 흐름을 한눈에 확인
""")
