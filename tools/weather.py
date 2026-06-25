"""
Weather Tool — OpenWeatherMap 5-Day Forecast API
Şehir ve tarih aralığına göre günlük hava durumu verisini çeker.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional

import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv(override=True)

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"
GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"


def _fetch_forecast(city: str) -> dict:
    """OpenWeatherMap 5-day/3-hour forecast API'den ham veriyi çeker."""
    if not OPENWEATHERMAP_API_KEY:
        raise ValueError(
            "OPENWEATHERMAP_API_KEY ortam değişkeni bulunamadı. "
            ".env dosyasına ekleyin."
        )

    # Önce Geocoding API ile şehrin en doğru koordinatlarını (lat, lon) alıyoruz
    geo_params = {
        "q": city,
        "limit": 1,
        "appid": OPENWEATHERMAP_API_KEY,
    }
    try:
        geo_response = requests.get(GEO_URL, params=geo_params, timeout=10)
        geo_response.raise_for_status()
        geo_data = geo_response.json()
    except Exception:
        geo_data = []

    # Eğer koordinat bulunabildiyse koordinat bazlı, bulunamadıysa q parametresi ile arama yapıyoruz
    if geo_data:
        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]
        params = {
            "lat": lat,
            "lon": lon,
            "appid": OPENWEATHERMAP_API_KEY,
            "units": "metric",
            "lang": "en",
        }
    else:
        params = {
            "q": city,
            "appid": OPENWEATHERMAP_API_KEY,
            "units": "metric",
            "lang": "en",
        }

    response = requests.get(BASE_URL, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def _aggregate_daily(forecast_data: dict, start_date: str, end_date: str) -> list[dict]:
    """
    3-saatlik veriyi günlük ortalamalara dönüştürür.
    Sadece start_date ile end_date aralığındaki günleri döndürür.
    """
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    daily: dict[str, list] = {}

    for entry in forecast_data.get("list", []):
        dt = datetime.fromtimestamp(entry["dt"]).date()
        if start <= dt <= end:
            date_str = dt.isoformat()
            if date_str not in daily:
                daily[date_str] = []
            daily[date_str].append(entry)

    result = []
    for date_str in sorted(daily.keys()):
        entries = daily[date_str]
        temps = [e["main"]["temp"] for e in entries]
        humidities = [e["main"]["humidity"] for e in entries]
        wind_speeds = [e["wind"]["speed"] * 3.6 for e in entries]  # m/s → km/h
        rain_total = sum(e.get("rain", {}).get("3h", 0) for e in entries)
        clouds = [e["clouds"]["all"] for e in entries]

        # En sık görülen hava durumu
        conditions = [e["weather"][0]["main"] for e in entries]
        main_condition = max(set(conditions), key=conditions.count)
        descriptions = [e["weather"][0]["description"] for e in entries]
        main_description = max(set(descriptions), key=descriptions.count)

        result.append({
            "date": date_str,
            "temp_avg": round(sum(temps) / len(temps), 1),
            "temp_min": round(min(temps), 1),
            "temp_max": round(max(temps), 1),
            "rain_total_mm": round(rain_total, 1),
            "wind_speed_avg_kmh": round(sum(wind_speeds) / len(wind_speeds), 1),
            "cloud_cover_avg": round(sum(clouds) / len(clouds), 1),
            "humidity_avg": round(sum(humidities) / len(humidities), 1),
            "condition": main_condition
        })

    return result


LAST_WEATHER_DATA = {}

@tool
def get_weather(city: str, start_date: str, end_date: str) -> str:
    """
    Belirtilen şehir ve tarih aralığı için günlük hava durumu tahminini döndürür.

    Args:
        city: Şehir adı (örn: "Istanbul", "Paris", "London")
        start_date: Başlangıç tarihi (YYYY-MM-DD formatında)
        end_date: Bitiş tarihi (YYYY-MM-DD formatında)

    Returns:
        JSON formatında günlük hava durumu verileri.
    """
    try:
        forecast_data = _fetch_forecast(city)
        daily_data = _aggregate_daily(forecast_data, start_date, end_date)
        
        # Scoring tool'u için veriyi cache'le
        LAST_WEATHER_DATA["data"] = daily_data

        if not daily_data:
            return json.dumps({
                "error": False,
                "city": city,
                "message": f"{start_date} ile {end_date} aralığında veri bulunamadı. "
                           "OpenWeatherMap sadece 5 günlük tahmin sunar.",
                "data": []
            }, ensure_ascii=False)

        return json.dumps({
            "error": False,
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
            "days_count": len(daily_data),
            "data": daily_data,
        }, ensure_ascii=False)

    except requests.exceptions.HTTPError as e:
        return json.dumps({
            "error": True,
            "message": f"API hatası: {e.response.status_code} — {e.response.text}"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "error": True,
            "message": f"Hata: {str(e)}"
        }, ensure_ascii=False)
