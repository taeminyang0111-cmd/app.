import streamlit as st
import requests
from openai import OpenAI
from datetime import date, timedelta
import pandas as pd

# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="AI 습관 트래커", page_icon="📊")
st.title("📊 AI 습관 트래커")
st.write("오늘의 습관 체크인 + 날씨/강아지 + AI 코치 리포트로 하루를 정리해요.")

# =========================
# 사이드바: API Key
# =========================
st.sidebar.header("🔑 API 설정")
OPENAI_API_KEY = st.sidebar.text_input("OpenAI API Key", type="password")
OWM_API_KEY = st.sidebar.text_input("OpenWeatherMap API Key", type="password")

if not OPENAI_API_KEY or not OWM_API_KEY:
    st.info("🔑 사이드바에서 OpenAI / OpenWeatherMap API Key를 입력해주세요.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# Session State 초기화: 6일 샘플 데이터
# =========================
def init_demo_history():
    today = date.today()
    demo = []
    # 6일치 샘플 (오늘 제외)
    # 달성습관: 0~5, 기분: 1~10
    samples = [
        (4, 7),
        (3, 6),
        (5, 8),
        (2, 5),
        (4, 7),
        (3, 6),
    ]
    for i, (ach, mood) in enumerate(reversed(samples), start=1):
        d = today - timedelta(days=i)
        demo.append({"date": d.isoformat(), "achieved": ach, "mood": mood})
    return demo

if "history" not in st.session_state:
    st.session_state["history"] = init_demo_history()

# =========================
# API 연동
# =========================
def get_weather(city: str, api_key: str):
    """OpenWeatherMap 현재 날씨. 한국어/섭씨. 실패 시 None"""
    try:
        res = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": api_key, "units": "metric", "lang": "kr"},
            timeout=10
        )
        res.raise_for_status()
        data = res.json()
        temp = data.get("main", {}).get("temp")
        desc = None
        w = (data.get("weather") or [])
        if w and isinstance(w, list):
            desc = w[0].get("description")
        return {
            "city": city,
            "temp_c": temp,
            "description": desc
        }
    except requests.RequestException:
        return None

def get_dog_image():
    """Dog CEO 랜덤 강아지 이미지 URL + 품종(가능하면). 실패 시 (None, None)"""
    try:
        res = requests.get("https://dog.ceo/api/breeds/image/random", timeout=10)
        res.raise_for_status()
        data = res.json()
        url = data.get("message")
        if not url:
            return None, None

        breed = None
        # URL 예: https://images.dog.ceo/breeds/hound-afghan/n02088094_1003.jpg
        try:
            parts = url.split("/breeds/")
            if len(parts) > 1:
                after = parts[1]
                breed_part = after.split("/")[0]  # hound-afghan
                breed = breed_part.replace("-", " ")
        except Exception:
            breed = None

        return url, breed
    except requests.RequestException:
        return None, None

# =========================
# AI 코치 리포트
# =========================
COACH_SYSTEM = {
    "스파르타 코치": (
        "너는 엄격하고 단호한 코치다. 변명은 받아주지 않는다. "
        "짧고 명확하게, 행동을 강하게 촉구한다. 과장된 위로는 하지 않는다."
    ),
    "따뜻한 멘토": (
        "너는 따뜻하고 현실적인 멘토다. 사용자의 노력을 인정하고, "
        "부담을 줄이면서도 꾸준히 이어갈 수 있는 실천을 제안한다."
    ),
    "게임 마스터": (
        "너는 RPG 게임 마스터다. 사용자는 주인공이며, 오늘의 성과를 경험치/퀘스트처럼 표현한다. "
        "너무 유치하지 않게, 몰입감 있는 톤으로 짧고 재밌게 진행한다."
    ),
}

def generate_report(
    coach_style: str,
    habit_status: dict,
    mood: int,
    weather: dict | None,
    dog_breed: str | None,
    completion_pct: int,
):
    """습관+기분+날씨+강아지 품종 -> OpenAI 리포트. 실패 시 None"""
    try:
        system_instructions = COACH_SYSTEM.get(coach_style, COACH_SYSTEM["따뜻한 멘토"])

        # 입력 구성
        habits_done = [k for k, v in habit_status.items() if v]
        habits_miss = [k for k, v in habit_status.items() if not v]

        weather_text = "날씨 정보 없음"
        if weather:
            city = weather.get("city")
            temp = weather.get("temp_c")
            desc = weather.get("description")
            weather_text = f"{city} / {temp}°C / {desc}"

        dog_text = dog_breed if dog_breed else "품종 정보 없음"

        user_input = f"""
[오늘 체크인]
- 달성률: {completion_pct}%
- 기분(1~10): {mood}
- 달성한 습관: {", ".join(habits_done) if habits_done else "없음"}
- 미달성 습관: {", ".join(habits_miss) if habits_miss else "없음"}
- 날씨: {weather_text}
- 오늘의 강아지 품종: {dog_text}

[출력 형식 (반드시 지켜라)]
컨디션 등급: <S/A/B/C/D 중 1개>
습관 분석: <2~4문장>
날씨 코멘트: <1~2문장>
내일 미션: <불릿 3개, 아주 구체적으로>
오늘의 한마디: <짧은 한 문장>
""".strip()

        resp = client.responses.create(
            model="gpt-5-mini",
            instructions=system_instructions,
            input=user_input,
            # 너무 길게 늘어지지 않게
            # (SDK/모델에 따라 무시될 수 있지만 안전하게 둠)
            max_output_tokens=450,
        )
        text = (resp.output_text or "").strip()
        return text if text else None
    except Exception:
        return None

# =========================
# 습관 체크인 UI
# =========================
st.subheader("✅ 오늘의 습관 체크인")

# 5개 체크박스 2열 배치
colA, colB = st.columns(2)
with colA:
    wake_mission = st.checkbox("🌅 기상 미션")
    water = st.checkbox("💧 물 마시기")
    study = st.checkbox("📚 공부/독서")
with colB:
    workout = st.checkbox("🏃 운동하기")
    sleep = st.checkbox("😴 수면")

mood = st.slider("🙂 오늘 기분은 어때요?", 1, 10, 6)

cities = ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon", "Gwangju", "Ulsan", "Suwon", "Jeju", "Sejong"]
city = st.selectbox("🏙️ 도시 선택", cities, index=0)

coach_style = st.radio(
    "🧑‍🏫 코치 스타일",
    ["스파르타 코치", "따뜻한 멘토", "게임 마스터"],
    horizontal=True
)

habit_status = {
    "기상 미션": wake_mission,
    "물 마시기": water,
    "공부/독서": study,
    "운동하기": workout,
    "수면": sleep,
}

achieved_count = sum(1 for v in habit_status.values() if v)
completion_pct = int(round((achieved_count / 5) * 100))

# =========================
# 달성률 + 차트
# =========================
st.subheader("📈 오늘의 지표")

m1, m2, m3 = st.columns(3)
m1.metric("달성률", f"{completion_pct}%")
m2.metric("달성 습관", f"{achieved_count}/5")
m3.metric("기분", f"{mood}/10")

# 오늘 기록 session_state 저장(차트용) — 리포트 생성 전에 미리 반영
def upsert_today_record():
    today_str = date.today().isoformat()
    history = st.session_state["history"]

    # 오늘 기록이 있으면 교체, 없으면 추가
    replaced = False
    for i, row in enumerate(history):
        if row.get("date") == today_str:
            history[i] = {"date": today_str, "achieved": achieved_count, "mood": mood}
            replaced = True
            break
    if not replaced:
        history.append({"date": today_str, "achieved": achieved_count, "mood": mood})

    # 날짜 기준 정렬 + 최근 30일만 유지(가볍게)
    history = sorted(history, key=lambda x: x.get("date", ""))
    st.session_state["history"] = history[-30:]

upsert_today_record()

# 최근 7일 데이터 구성 (6일 샘플 + 오늘)
today = date.today()
last7 = []
hist_map = {h["date"]: h for h in st.session_state["history"] if "date" in h}
for i in range(6, -1, -1):
    d = today - timedelta(days=i)
    key = d.isoformat()
    row = hist_map.get(key)
    if row:
        last7.append({"날짜": key[5:], "달성습관": row["achieved"], "기분": row["mood"]})
    else:
        last7.append({"날짜": key[5:], "달성습관": 0, "기분": 5})

df7 = pd.DataFrame(last7)

st.caption("최근 7일 달성 습관(0~5)")
st.bar_chart(df7.set_index("날짜")[["달성습관"]])

# =========================
# 결과 표시: 컨디션 리포트 생성
# =========================
st.subheader("🧠 AI 코치 리포트")

if st.button("컨디션 리포트 생성"):
    with st.spinner("날씨/강아지/리포트를 준비 중..."):
        weather = get_weather(city, OWM_API_KEY)
        dog_url, dog_breed = get_dog_image()

        report = generate_report(
            coach_style=coach_style,
            habit_status=habit_status,
            mood=mood,
            weather=weather,
            dog_breed=dog_breed,
            completion_pct=completion_pct,
        )

    # 날씨 + 강아지 카드(2열)
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### 🌦️ 오늘 날씨")
        if weather:
            temp = weather.get("temp_c")
            desc = weather.get("description")
            st.write(f"**{weather.get('city')}**")
            st.write(f"- 기온: **{temp}°C**" if temp is not None else "- 기온: 정보 없음")
            st.write(f"- 상태: **{desc}**" if desc else "- 상태: 정보 없음")
        else:
            st.warning("날씨 정보를 가져오지 못했어요.")

    with c2:
        st.markdown("### 🐶 오늘의 강아지")
        if dog_url:
            st.image(dog_url, use_container_width=True)
            st.caption(f"품종: {dog_breed}" if dog_breed else "품종: (알 수 없음)")
        else:
            st.warning("강아지 사진을 가져오지 못했어요.")

    st.markdown("---")
    st.markdown("### 🧾 리포트")
    if report:
        st.write(report)
    else:
        st.error("AI 리포트 생성에 실패했어요. API Key/네트워크를 확인해주세요.")

    # 공유용 텍스트
    share_lines = [
        f"[AI 습관 트래커] {date.today().isoformat()}",
        f"- 도시: {city}",
        f"- 달성률: {completion_pct}% ({achieved_count}/5)",
        f"- 기분: {mood}/10",
        f"- 달성: {', '.join([k for k, v in habit_status.items() if v]) or '없음'}",
        f"- 날씨: {(weather.get('temp_c') if weather else 'NA')}°C / {(weather.get('description') if weather else 'NA')}",
        f"- 강아지: {dog_breed or 'NA'}",
        "",
        "[AI 코치 리포트]",
        report or "(리포트 생성 실패)",
    ]
    st.markdown("### 📌 공유용 텍스트")
    st.code("\n".join(share_lines), language="text")

# =========================
# 하단: API 안내
# =========================
with st.expander("📎 API 안내 / 준비물"):
    st.markdown(
        """
**필요한 키**
- OpenAI API Key: OpenAI 플랫폼에서 발급
- OpenWeatherMap API Key: OpenWeatherMap에서 발급

**사용 API**
- OpenWeatherMap Current Weather: 한국어(lang=kr), 섭씨(units=metric)
- Dog CEO Random Image: 랜덤 강아지 이미지

**주의**
- 네트워크/키 오류 시 날씨·강아지·리포트가 실패할 수 있어요.
- 이 앱은 학습/데모 목적이며, 건강/의학 판단을 대신하지 않습니다.
"""
    )
