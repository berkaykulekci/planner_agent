"""
Streamlit UI — Agentic AI Travel Planner Web Arayüzü
"""

import sys
import os

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime, timedelta
import json

from agent.planner import run_planner_agent, format_react_steps
from agent.memory import save_search, get_recent_searches
from evaluation.evaluator import evaluate_itinerary
from agent.postcard import generate_postcard
from agent.lingo import generate_local_lingo


# ─────────────────────────── Sayfa Konfigürasyonu ───────────────────────────

st.set_page_config(
    page_title="🌍 AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────── Custom CSS ───────────────────────────

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@500;700&family=Playfair+Display:ital,wght@1,600&display=swap" rel="stylesheet">
<style>
    /* Ana tema */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }

    /* Başlık */
    .main-title {
        text-align: center;
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 50%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        font-family: 'Inter', sans-serif;
    }

    .sub-title {
        text-align: center;
        color: #a0a0b0;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Kartlar */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: transform 0.2s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(255, 255, 255, 0.2);
    }

    /* ReAct Steps */
    .react-thought {
        background: rgba(79, 172, 254, 0.1);
        border-left: 4px solid #4facfe;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
        color: #c0d0ff;
    }

    .react-action {
        background: rgba(240, 147, 251, 0.1);
        border-left: 4px solid #f093fb;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
        color: #e0c0ff;
    }

    .react-observation {
        background: rgba(67, 233, 123, 0.1);
        border-left: 4px solid #43e97b;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
        color: #c0ffd0;
        font-size: 0.85rem;
    }

    /* Skor badge */
    .score-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 1.3rem;
    }

    .score-high { background: rgba(67, 233, 123, 0.2); color: #43e97b; }
    .score-mid { background: rgba(250, 215, 75, 0.2); color: #fad74b; }
    .score-low { background: rgba(245, 87, 108, 0.2); color: #f5576c; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Genel düzenlemeler */
    .stMarkdown h3 {
        color: #e0e0f0;
    }

    div[data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
    }

    /* Kartpostal Tasarımı */
    .postcard-container {
        background: #fdfaf2;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        padding: 1.5rem;
        border: 8px double #d3b88a;
        margin-bottom: 1.5rem;
        color: #2c2519;
    }

    .postcard-title {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 1.8rem;
        color: #6e473b;
        text-align: center;
        margin-bottom: 1rem;
        border-bottom: 2px solid #e8dfc7;
        padding-bottom: 0.5rem;
    }

    .postcard-back {
        display: flex;
        gap: 1.5rem;
        min-height: 250px;
    }

    .postcard-message-column {
        flex: 1.3;
        font-family: 'Caveat', cursive;
        font-size: 1.45rem;
        line-height: 1.4;
        color: #3d3124;
        padding-right: 1rem;
        border-right: 2px dashed #e8dfc7;
        white-space: pre-line;
    }

    .postcard-address-column {
        flex: 0.7;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding-left: 0.5rem;
        position: relative;
    }

    .postcard-stamp {
        align-self: flex-end;
        width: 70px;
        height: 85px;
        border: 2px dashed #a08060;
        background: #f4ecd8;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        border-radius: 4px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }

    .postcard-address-lines {
        margin-top: auto;
    }

    .postcard-address-line {
        border-bottom: 1px solid #a08060;
        height: 35px;
        font-family: 'Caveat', cursive;
        font-size: 1.25rem;
        color: #5d4a36;
        display: flex;
        align-items: flex-end;
        padding-left: 5px;
    }

    /* Lingo Kartları Tasarımı */
    .lingo-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1rem;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .lingo-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.2rem;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .lingo-card:hover {
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(79, 172, 254, 0.4);
        box-shadow: 0 10px 20px rgba(79, 172, 254, 0.1);
    }

    .lingo-phrase {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.3rem;
        color: #4facfe;
        margin-bottom: 0.5rem;
    }

    .lingo-pronunciation {
        font-size: 0.9rem;
        color: #f093fb;
        margin-bottom: 0.8rem;
        font-style: italic;
    }

    .lingo-meaning {
        font-size: 1rem;
        color: #ffffff;
        font-weight: 600;
        margin-bottom: 0.8rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        padding-top: 0.5rem;
    }

    .lingo-context {
        font-size: 0.8rem;
        color: #a0a0b0;
        line-height: 1.3;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────── Header ───────────────────────────

st.markdown('<h1 class="main-title">✈️ AI Travel Planner</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-title">Hava durumuna göre akıllı seyahat planı oluşturan otonom AI ajanı</p>',
    unsafe_allow_html=True,
)


# ─────────────────────────── Sidebar ───────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Ayarlar")

    city = st.text_input(
        "🏙️ Şehir",
        value="Istanbul",
        placeholder="Şehir adı girin...",
        help="İngilizce şehir adı girin (örn: Istanbul, Paris, London)",
    )

    col1, col2 = st.columns(2)
    today = datetime.now().date()
    with col1:
        start_date = st.date_input(
            "📅 Başlangıç",
            value=today + timedelta(days=1),
            min_value=today,
            max_value=today + timedelta(days=4),
        )
    with col2:
        end_date = st.date_input(
            "📅 Bitiş",
            value=min(today + timedelta(days=4), today + timedelta(days=4)),
            min_value=today,
            max_value=today + timedelta(days=4),
        )

    preference = st.selectbox(
        "🎯 Aktivite Tercihi",
        options=["both", "outdoor", "indoor"],
        format_func=lambda x: {
            "outdoor": "🌿 Açık Hava",
            "indoor": "🏛️ Kapalı Mekan",
            "both": "🔄 Her İkisi",
        }[x],
    )

    persona = st.selectbox(
        "🎭 Seyahat Karakteri",
        options=["standard", "gourmet", "history", "budget"],
        format_func=lambda x: {
            "standard": "👤 Standart Rehber",
            "gourmet": "🍽️ Gurme Şef",
            "history": "🏛️ Tarih Profesörü",
            "budget": "🎒 Tasarrufçu Gezgin",
        }[x],
        help="Ajanın planı yaparken bürüneceği kişiliği seçin.",
    )

    st.markdown("---")

    # Geçmiş aramalar
    st.markdown("### 📋 Son Aramalar")
    recent = get_recent_searches(5)
    if recent:
        for search in reversed(recent):
            pref_emoji = {"outdoor": "🌿", "indoor": "🏛️", "both": "🔄"}.get(
                search.get("preference", "both"), "🔄"
            )
            st.caption(
                f"{pref_emoji} {search['city']} | "
                f"{search['start_date']} → {search['end_date']}"
            )
    else:
        st.caption("Henüz arama yapılmadı.")

    st.markdown("---")
    st.markdown(
        "### ℹ️ Hakkında\n"
        "Bu uygulama **ReAct pattern** ile çalışan "
        "otonom bir AI ajanı kullanır.\n\n"
        "- 🌤️ Gerçek hava durumu verisi\n"
        "- 📊 Çok boyutlu skorlama\n"
        "- 🤖 LLM değerlendirmesi"
    )


# ─────────────────────────── Ana İçerik ───────────────────────────

# Tarih doğrulama
if start_date > end_date:
    st.error("⚠️ Başlangıç tarihi bitiş tarihinden sonra olamaz!")
    st.stop()

# Plan oluştur butonu
run_button = st.button(
    "🚀 Seyahat Planı Oluştur",
    type="primary",
    use_container_width=True,
)

if run_button:
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    # Aramayı kaydet
    save_search(city, start_str, end_str, preference)

    # ─── Adım 1: Agent Çalıştır ───
    with st.status("🤖 AI Agent çalışıyor...", expanded=True) as status:
        st.write("🔄 ReAct döngüsü başlatılıyor...")
        st.write(f"📍 Şehir: **{city}**")
        st.write(f"📅 Tarih: **{start_str}** → **{end_str}**")

        try:
            result = run_planner_agent(
                city=city,
                start_date=start_str,
                end_date=end_str,
                preference=preference,
                persona=persona,
            )
            st.write("✉️ Seyahat kartpostalı hazırlanıyor...")
            result["postcard"] = generate_postcard(
                city=city,
                itinerary=result["output"],
                persona=persona
            )
            st.write("💡 Yerel dil rehberi hazırlanıyor...")
            result["lingo"] = generate_local_lingo(
                city=city,
                persona=persona
            )
            status.update(label="✅ Plan, Kartpostal ve Dil Rehberi oluşturuldu!", state="complete")
        except Exception as e:
            status.update(label="❌ Hata oluştu", state="error")
            st.error(f"Agent hatası: {str(e)}")
            st.stop()

    # ─── Adım 2: ReAct Adımlarını Göster ───
    st.markdown("---")
    with st.expander("🧠 ReAct Döngüsü (Agent Düşünce Süreci)", expanded=False):
        steps = format_react_steps(result.get("intermediate_steps", []))
        if steps:
            for step in steps:
                if step["type"] == "thought":
                    st.markdown(
                        f'<div class="react-thought">💭 <b>Thought:</b> {step["content"]}</div>',
                        unsafe_allow_html=True,
                    )
                elif step["type"] == "action":
                    st.markdown(
                        f'<div class="react-action">⚡ <b>Action:</b> {step["content"]}</div>',
                        unsafe_allow_html=True,
                    )
                elif step["type"] == "observation":
                    st.markdown(
                        f'<div class="react-observation">👁️ <b>Observation:</b> {step["content"]}</div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.info("Ara adım verisi mevcut değil.")

    # ─── Adım 3: Hava Durumu Özeti ───
    weather_data = result.get("weather_data")
    scores_data = result.get("scores")

    if weather_data and not weather_data.get("error"):
        st.markdown("### 🌤️ Hava Durumu Özeti")
        days = weather_data.get("data", [])
        if days:
            cols = st.columns(min(len(days), 5))
            for i, day in enumerate(days):
                condition_emoji = {
                    "Clear": "☀️",
                    "Clouds": "☁️",
                    "Rain": "🌧️",
                    "Drizzle": "🌦️",
                    "Thunderstorm": "⛈️",
                    "Snow": "🌨️",
                    "Mist": "🌫️",
                    "Fog": "🌫️",
                }.get(day.get("condition", ""), "🌡️")

                with cols[i % len(cols)]:
                    st.markdown(
                        f"""<div class="metric-card">
                        <h4 style="color:#a0a0b0; margin:0;">{day['date']}</h4>
                        <p style="font-size:2rem; margin:0.3rem 0;">{condition_emoji}</p>
                        <p style="color:#fff; font-size:1.1rem; margin:0;">
                            🌡️ {day['temp_avg']}°C
                        </p>
                        <p style="color:#a0a0b0; font-size:0.85rem; margin:0;">
                            {day['temp_min']}° / {day['temp_max']}°
                        </p>
                        <p style="color:#a0a0b0; font-size:0.85rem; margin:0;">
                            💧 {day['rain_total_mm']}mm · 💨 {day['wind_speed_avg_kmh']}km/h
                        </p>
                        </div>""",
                        unsafe_allow_html=True,
                    )

    # ─── Adım 4: Skor Tablosu ───
    if scores_data and not scores_data.get("error"):
        st.markdown("### 📊 Günlük Skorlar (En İyiden En Kötüye)")
        scored_days = scores_data.get("scored_days", [])
        if scored_days:
            for day in scored_days:
                score = day["score"]
                if score >= 7:
                    score_class = "score-high"
                elif score >= 4:
                    score_class = "score-mid"
                else:
                    score_class = "score-low"

                breakdown = day.get("breakdown", {})
                weather_sum = day.get("weather_summary", {})

                st.markdown(
                    f"""<div class="metric-card" style="display:flex; align-items:center; gap:1.5rem;">
                    <div>
                        <span class="score-badge {score_class}">{score}/10</span>
                    </div>
                    <div style="flex:1;">
                        <h4 style="color:#fff; margin:0;">{day['date']} — {day['category']}</h4>
                        <p style="color:#a0a0b0; margin:0.3rem 0; font-size:0.9rem;">
                            🌡️ Sıcaklık: {breakdown.get('temperature', '-')}/4 · 
                            💧 Yağmur: {breakdown.get('rain', '-')}/3 · 
                            💨 Rüzgar: {breakdown.get('wind', '-')}/1.5 · 
                            ☁️ Bulut: {breakdown.get('cloud_cover', '-')}/1 · 
                            💦 Nem: {breakdown.get('humidity', '-')}/0.5
                        </p>
                        <p style="color:#c0c0d0; margin:0; font-size:0.85rem;">
                            Öneri: <b>{"🌿 Outdoor" if day['recommendation'] == 'outdoor' else "🏛️ Indoor" if day['recommendation'] == 'indoor' else "🔄 Karma"}</b>
                            · {weather_sum.get('condition', '')} · {weather_sum.get('temp_avg', '')}°C
                        </p>
                    </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    # ─── Adım 5: Final Plan ───
    st.markdown("### 📝 Seyahat Planı")
    st.markdown(
        f'<div class="metric-card">{result["output"]}</div>',
        unsafe_allow_html=True,
    )

    # ─── Adım 5.5: Yapay Zeka Kartpostalı ───
    if "postcard" in result:
        st.markdown("### ✉️ Gelecekten Gelen Seyahat Kartpostalınız")
        postcard = result["postcard"]
        
        # Kartpostal arka yüz tasarımı için ikon ve adres belirleme
        stamp_emoji = {
            "gourmet": "🥐",
            "history": "🏛️",
            "budget": "🎒",
            "standard": "✈️"
        }.get(persona, "✈️")
        
        persona_address = {
            "gourmet": "Lezzet Kaşifleri Kulübü",
            "history": "Zaman Yolcuları Derneği",
            "budget": "Sırt Çantalı Gezginler Ocağı",
            "standard": "Meraklı Kaşifler Cemiyeti"
        }.get(persona, "Meraklı Kaşifler Cemiyeti")

        postcard_html = (
            f'<div class="postcard-container">'
            f'<div class="postcard-title">Greetings from {city}!</div>'
            f'<div class="postcard-back">'
            f'<div class="postcard-message-column">{postcard["postcard_message"]}</div>'
            f'<div class="postcard-address-column">'
            f'<div class="postcard-stamp">{stamp_emoji}</div>'
            f'<div class="postcard-address-lines">'
            f'<div class="postcard-address-line">Kime: {persona_address}</div>'
            f'<div class="postcard-address-line">Adres: Bulutların Üstü, Gezegen Dünya</div>'
            f'<div class="postcard-address-line">Posta Kodu: 00000</div>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        
        col_front, col_back = st.columns([1, 1.1])
        with col_front:
            st.image(
                postcard["image_url"], 
                use_container_width=True, 
                caption=f"🖼️ Yapay Zeka Tasarımı {city} Görseli (Pollinations.ai)"
            )
        with col_back:
            st.markdown(postcard_html, unsafe_allow_html=True)

    # ─── Adım 5.6: Yerel Kültür & Dil Asistanı ───
    if "lingo" in result:
        lingo_data = result["lingo"]
        st.markdown(f"### 💡 Yerel Dil Asistanı ({lingo_data.get('language', 'Yerel Dil')})")
        
        cards_html = ""
        for item in lingo_data.get("phrases", []):
            cards_html += (
                f'<div class="lingo-card">'
                f'<div>'
                f'<div class="lingo-phrase">{item["phrase"]}</div>'
                f'<div class="lingo-pronunciation">🗣️ {item["pronunciation"]}</div>'
                f'</div>'
                f'<div>'
                f'<div class="lingo-meaning">🇹🇷 {item["meaning"]}</div>'
                f'<div class="lingo-context">💡 {item["context"]}</div>'
                f'</div>'
                f'</div>'
            )
        
        st.markdown(
            f'<div class="lingo-container">{cards_html}</div>',
            unsafe_allow_html=True
        )

    # ─── Adım 6: Evaluation Agent ───
    st.markdown("---")
    with st.status("🔍 Değerlendirme Ajanı çalışıyor...", expanded=True) as eval_status:
        st.write("📋 Plan kalitesi analiz ediliyor...")
        try:
            eval_result = evaluate_itinerary(
                weather_data=weather_data,
                scores_data=scores_data,
                itinerary=result["output"],
                city=city,
            )
            eval_status.update(label="✅ Değerlendirme tamamlandı!", state="complete")
        except Exception as e:
            eval_status.update(label="❌ Değerlendirme hatası", state="error")
            st.error(f"Evaluation hatası: {str(e)}")
            eval_result = None

    if eval_result:
        st.markdown("### 🏆 Plan Değerlendirmesi")
        eval_score = eval_result["score"]
        if eval_score >= 7:
            score_class = "score-high"
            emoji = "🟢"
        elif eval_score >= 4:
            score_class = "score-mid"
            emoji = "🟡"
        else:
            score_class = "score-low"
            emoji = "🔴"

        st.markdown(
            f"""<div class="metric-card">
            <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">
                <span class="score-badge {score_class}">{emoji} {eval_score}/10</span>
                <span style="color:#a0a0b0; font-size:1rem;">Evaluation Agent Skoru</span>
            </div>
            </div>""",
            unsafe_allow_html=True,
        )

        with st.expander("📖 Detaylı Değerlendirme", expanded=True):
            st.markdown(eval_result["evaluation_text"])
