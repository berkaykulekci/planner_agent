"""
Evaluation Agent — Oluşturulan seyahat planını ikinci bir LLM ile değerlendirir.
"""

import os
import json

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from agent.prompts import EVALUATION_SYSTEM_PROMPT

load_dotenv(override=True)


def _create_evaluator_llm() -> ChatGroq:
    """Değerlendirme için ayrı bir LLM instance'ı oluşturur."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY ortam değişkeni bulunamadı.")

    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        groq_api_key=api_key,
        temperature=0.1,  # Daha deterministik değerlendirme
        max_retries=3,
    )


def evaluate_itinerary(
    weather_data: dict | None,
    scores_data: dict | None,
    itinerary: str,
    city: str,
) -> dict:
    """
    Oluşturulan seyahat planını değerlendirir.

    Args:
        weather_data: Hava durumu verisi (dict)
        scores_data: Skorlama sonuçları (dict)
        itinerary: Agent'ın oluşturduğu plan (string)
        city: Şehir adı

    Returns:
        dict: {
            "score": int (0-10),
            "evaluation_text": str (detaylı değerlendirme),
            "raw_response": str
        }
    """
    llm = _create_evaluator_llm()

    # Hava durumu özetini hazırla
    weather_summary = "Hava durumu verisi mevcut değil."
    if weather_data and not weather_data.get("error"):
        days = weather_data.get("data", [])
        if days:
            lines = []
            for day in days:
                lines.append(
                    f"- {day['date']}: {day['temp_avg']}°C, "
                    f"Yağış: {day['rain_total_mm']}mm, "
                    f"Rüzgar: {day['wind_speed_avg_kmh']}km/h, "
                    f"Durum: {day['condition']}"
                )
            weather_summary = "\n".join(lines)

    # Skor özetini hazırla
    scores_summary = "Skor verisi mevcut değil."
    if scores_data and not scores_data.get("error"):
        scored_days = scores_data.get("scored_days", [])
        if scored_days:
            lines = []
            for day in scored_days:
                lines.append(
                    f"- {day['date']}: Skor {day['score']}/10 "
                    f"({day['category']}) — Öneri: {day['recommendation']}"
                )
            scores_summary = "\n".join(lines)

    evaluation_input = f"""
## Değerlendirilecek Seyahat Planı

**Şehir**: {city}

### Hava Durumu Verileri
{weather_summary}

### Günlük Skorlar
{scores_summary}

### Oluşturulan Plan
{itinerary}

---

Yukarıdaki planı değerlendirme kriterlerine göre analiz et ve puanla.
"""

    messages = [
        SystemMessage(content=EVALUATION_SYSTEM_PROMPT),
        HumanMessage(content=evaluation_input),
    ]

    response = llm.invoke(messages)
    response_text = response.content

    # Skorun parse edilmesi
    score = _extract_score(response_text)

    return {
        "score": score,
        "evaluation_text": response_text,
        "raw_response": response_text,
    }


def _extract_score(text: str) -> float:
    """Değerlendirme metninden skoru çıkarır."""
    import re

    # "Skor: X/10" veya "Score: X/10" pattern'ini ara (Ondalıklı sayıları da destekler)
    patterns = [
        r"[Ss]kor:\s*([\d.]+)\s*/\s*10",
        r"[Ss]core:\s*([\d.]+)\s*/\s*10",
        r"\*\*[Ss]kor:\s*([\d.]+)\s*/\s*10\*\*",
        r"\*\*[Ss]core:\s*([\d.]+)\s*/\s*10\*\*",
        r"([\d.]+)\s*/\s*10",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                score = float(match.group(1))
                return min(10.0, max(0.0, score))
            except ValueError:
                continue

    return 5.0  # Varsayılan skor
