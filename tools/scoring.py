"""
Scoring Tool — Günlük hava durumu skorlama
Her gün için 0-10 arası bir açık hava uygunluk skoru hesaplar.
"""

import json
from langchain_core.tools import tool


def _score_day(
    temp: float,
    rain_mm: float,
    wind_speed_kmh: float,
    cloud_cover: float = 50.0,
    humidity: float = 50.0,
) -> dict:
    """
    Tek bir gün için hava durumu skoru hesaplar.

    Scoring Logic:
    - Sıcaklık (max 4 puan): 20-26°C ideal, uzaklaştıkça düşer
    - Yağmur (max 3 puan ceza): 0mm = 3 puan, >10mm = 0 puan
    - Rüzgar (max 1.5 puan ceza): 0km/h = 1.5 puan, >40km/h = 0 puan
    - Bulutluluk (max 1 puan): 0% = 1 puan, 100% = 0 puan
    - Nem (max 0.5 puan): 40-60% ideal

    Returns:
        dict: score (0-10), breakdown detayları
    """
    # --- Sıcaklık Skoru (0-4) ---
    ideal_low, ideal_high = 20.0, 26.0
    if ideal_low <= temp <= ideal_high:
        temp_score = 4.0
    elif temp < ideal_low:
        diff = ideal_low - temp
        temp_score = max(0, 4.0 - (diff * 0.3))
    else:
        diff = temp - ideal_high
        temp_score = max(0, 4.0 - (diff * 0.3))

    # --- Yağmur Skoru (0-3) ---
    if rain_mm <= 0.1:
        rain_score = 3.0
    elif rain_mm <= 2.0:
        rain_score = 2.0
    elif rain_mm <= 5.0:
        rain_score = 1.0
    elif rain_mm <= 10.0:
        rain_score = 0.5
    else:
        rain_score = 0.0

    # --- Rüzgar Skoru (0-1.5) ---
    if wind_speed_kmh <= 10:
        wind_score = 1.5
    elif wind_speed_kmh <= 20:
        wind_score = 1.2
    elif wind_speed_kmh <= 30:
        wind_score = 0.7
    elif wind_speed_kmh <= 40:
        wind_score = 0.3
    else:
        wind_score = 0.0

    # --- Bulutluluk Skoru (0-1) ---
    cloud_score = max(0, 1.0 - (cloud_cover / 100.0))

    # --- Nem Skoru (0-0.5) ---
    if 40 <= humidity <= 60:
        humidity_score = 0.5
    elif humidity < 40:
        humidity_score = max(0, 0.5 - abs(40 - humidity) * 0.015)
    else:
        humidity_score = max(0, 0.5 - abs(humidity - 60) * 0.015)

    total = round(temp_score + rain_score + wind_score + cloud_score + humidity_score, 1)
    total = min(10.0, max(0.0, total))

    # Kategori belirleme
    if total >= 8:
        category = "Mükemmel ☀️"
        recommendation = "outdoor"
    elif total >= 6:
        category = "İyi 🌤️"
        recommendation = "outdoor"
    elif total >= 4:
        category = "Orta 🌥️"
        recommendation = "mixed"
    elif total >= 2:
        category = "Kötü 🌧️"
        recommendation = "indoor"
    else:
        category = "Çok Kötü ⛈️"
        recommendation = "indoor"

    return {
        "score": total,
        "category": category,
        "recommendation": recommendation,
        "breakdown": {
            "temperature": round(temp_score, 1),
            "rain": round(rain_score, 1),
            "wind": round(wind_score, 1),
            "cloud_cover": round(cloud_score, 1),
            "humidity": round(humidity_score, 1),
        },
    }


from tools.weather import LAST_WEATHER_DATA

@tool
def score_days() -> str:
    """
    En son çekilen hava durumu verisini (get_weather'dan) bellekte okuyup her gün için 0-10 arası
    açık hava uygunluk skoru hesaplar ve en iyi günlerden kötüye doğru sıralar.
    
    Bu aracı çağırırken HİÇBİR parametre girmemelisin. Sadece fonksiyonu çalıştır.

    Returns:
        JSON formatında her gün için skor, kategori ve öneriler.
    """
    try:
        weather_data = LAST_WEATHER_DATA.get("data", [])

        if not weather_data:
            return json.dumps({
                "error": True,
                "message": "Önce get_weather aracını kullanarak hava durumunu çekmelisiniz."
            }, ensure_ascii=False)

        scored_days = []
        for day in weather_data:
            result = _score_day(
                temp=day.get("temp_avg", 20),
                rain_mm=day.get("rain_total_mm", 0),
                wind_speed_kmh=day.get("wind_speed_avg_kmh", 0),
                cloud_cover=day.get("cloud_cover_avg", 50),
                humidity=day.get("humidity_avg", 50),
            )
            scored_days.append({
                "date": day.get("date", "unknown"),
                "score": result["score"],
                "category": result["category"],
                "recommendation": result["recommendation"],
                "breakdown": result["breakdown"],
                "weather_summary": {
                    "temp_avg": day.get("temp_avg"),
                    "rain_total_mm": day.get("rain_total_mm"),
                    "wind_speed_avg_kmh": day.get("wind_speed_avg_kmh"),
                    "condition": day.get("condition", "N/A"),
                },
            })

        # En iyi skordan en kötüye sırala
        scored_days.sort(key=lambda x: x["score"], reverse=True)

        return json.dumps({
            "error": False,
            "scored_days": scored_days,
            "best_day": scored_days[0] if scored_days else None,
            "worst_day": scored_days[-1] if scored_days else None,
        }, ensure_ascii=False)

    except json.JSONDecodeError as e:
        return json.dumps({
            "error": True,
            "message": f"JSON parse hatası: {str(e)}"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "error": True,
            "message": f"Scoring hatası: {str(e)}"
        }, ensure_ascii=False)
