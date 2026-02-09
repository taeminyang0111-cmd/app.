# app.py
import os
import re
import random
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

st.sidebar.caption("※ OpenAI 없이도 전체 기능 사용 가능")


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
def weather_habit_synergy(weather):
    if not weather:
        return "🌱 날씨 정보 없음 → 오늘은 핵심 습관 1~2개만 해도 충분해요."

    desc = weather["description"]
    temp = weather["temp"]

    if any(x in desc for x in ["비", "눈"]):
        return "☔ 비 오는 날! 실내 스트레칭 + 독서 조합 추천"
    if temp >= 30:
        return "🔥 더운 날씨! 물 마시기 + 휴식이 핵심"
    if temp <= 0:
        return "❄️ 추운 날씨! 수면 관리 + 가벼운 스트레칭"
    if "맑" in desc:
        return "☀️ 맑은 날씨! 산책 겸 운동 미션 도전!"

    return "🌤️ 무난한 날씨! 컨디션에 맞춰 균형 있게"


# =============================
# 🏅 Streak & Badge
# =============================
def calculate_streak(history):
    streak = 0
    for day in reversed(history):
        if day["rate"] >= 60:
            streak += 1
        else:
            break
    return streak


def streak_badge(streak):
    if streak >= 21:
        return "🏆 습관 마스터", "21일 연속! 습관이 정체성이 됐어요."
    if streak >= 7:
        return "🔥 7일 스트릭", "일주일 연속 성공!"
    if streak >= 3:
        return "✨ 3일 스타터", "아주 좋은 출발이에요."
    return None, None


# =============================
# 🐶 오늘의 동료
# =============================
DOG_PERSONA = {
    "retriever": "오늘은 사람들과의 협력이 행운 포인트",
    "shepherd": "집중력이 운을 부르는 날",
    "bulldog": "느려도 포기하지 않으면 성과 있음",
    "poodle": "계획을 세울수록 흐름이 좋아짐",
    "shiba": "혼자만의 리듬을 지키면 운이 열림",
    "husky": "몸을 움직일수록 기회가 따라옴",
}


def dog_fortune_hint(breed):
    for key, msg in DOG_PERSONA.items():
        if key in breed.lower():
            return msg
    return "오늘은 꾸준함이 최고의 행운이에요"


# =============================
# 🔮 오늘의 운세
# =============================
def today_fortune(mood, weather, breed):
    fortune_pool = []

    # 기분 기반
    if mood <= 4:
        fortune_pool.append("무리하지 말수록 오늘은 더 잘 풀려요.")
    elif mood >= 8:
        fortune_pool.append("에너지가 높은 날! 작은 도전이 큰 성과로 이어질 수 있어요.")
    else:
        fortune_pool.append("평균적인 흐름, 루틴을 지키면 안정적이에요.")

    # 날씨 기반
    if weather:
        if any(x in weather["description"] for x in ["비", "눈"]):
            fortune_pool.append("속도를 늦추면 오히려 실수가 줄어요.")
        elif "맑" in weather["description"]:
            fortune_pool.append("바깥 활동에서 좋은 기운이 들어와요.")

    # 동료 기반
    fortune_pool.append(dog_fortune_hint(breed))

    return " ".join(random.sample(fortune_pool, k=min(2, len(fortune_pool))))


# =============================
# Session State
# =============================
if "history" not in st.session_state:
    today = datetime.now().date()
    demo_rates = [40, 60, 80, 20, 100, 60]
    st.session_state.history = [
        {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "rate": r}
        for i, r in zip(range(6, 0, -1), demo_rates)
    ] + [{"date": today.strftime("%Y-%m-%d"), "rate": 0}]


# =============================
# Main UI
# =============================
st.title("📊 AI 습관 트래커")
st.caption("날씨 · 연속성 · 동료 · 오늘의 운세까지")

# --- Habit Check
st.subheader("✅ 오늘의 습관 체크인")

habits = ["🌅 기상", "💧 물", "📚 독서", "🏃 운동", "😴 수면"]

col1, col2 = st.columns(2)
checked = []

with col1:
    for h in habits[:3]:
        if st.checkbox(h):
            checked.append(h)

with col2:
    for h in habits[3:]:
        if st.checkbox(h):
            checked.append(h)

mood = st.slider("🙂 오늘 기분 점수", 1, 10, 7)

city = st.selectbox(
    "📍 도시 선택",
    ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon",
     "Gwangju", "Ulsan", "Suwon", "Seongnam", "Jeju"],
)

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
st.session_state.history[-1] = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "rate": rate,
}

# --- Streak
streak = calculate_streak(st.session_state.history)
badge, badge_msg = streak_badge(streak)

st.subheader("🏅 연속 달성")
st.write(f"🔥 {streak}일 연속")

if badge:
    st.success(f"{badge} – {badge_msg}")

# --- Chart
st.subheader("📈 최근 7일 달성률")
df = pd.DataFrame(st.session_state.history).set_index("date")
st.bar_chart(df)

# --- Dog & Fortune
dog = get_dog_image()
if dog:
    st.subheader("🐶 오늘의 동료 & 🔮 오늘의 운세")
    colA, colB = st.columns([1, 2])

    with colA:
        st.image(dog["url"], use_container_width=True)

    with colB:
        fortune = today_fortune(mood, weather, dog["breed"])
        st.markdown(f"**품종**: {dog['breed']}")
        st.success(f"🔮 오늘의 운세\n\n{fortune}")

# --- Footer
with st.expander("ℹ️ 이 기능의 의도"):
    st.markdown("""
- 🔮 **운세**는 미신이 아니라 *행동 프레이밍 도구*
- 날씨·기분·동료 캐릭터를 활용해
  오늘을 조금 더 긍정적으로 해석하도록 돕습니다
- 교육용: 조건 분기 + UX 설계 예제로 활용 가능
""")
