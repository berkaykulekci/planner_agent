"""
Postcard Generator — Seyahat planına göre yapay zeka destekli kartpostal üretir.
"""

import os
import re
import json
import urllib.parse
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from agent.prompts import POSTCARD_SYSTEM_PROMPT

load_dotenv(override=True)


def _create_postcard_llm() -> ChatGroq:
    """Kartpostal üretimi için LLM instance'ı oluşturur."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY ortam değişkeni bulunamadı. .env dosyasına ekleyin.")

    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        groq_api_key=api_key,
        temperature=0.7,  # Kartpostal mesajlarının daha yaratıcı ve samimi olması için daha yüksek sıcaklık
        max_retries=3,
    )


def generate_postcard(city: str, itinerary: str, persona: str) -> dict:
    """
    Seyahat planı ve karakterine göre kartpostal içeriği üretir.

    Args:
        city: Şehir adı
        itinerary: Seyahat planı (metin)
        persona: Kullanıcının seçtiği karakter

    Returns:
        dict: {
            "image_prompt": str,
            "postcard_message": str,
            "image_url": str
        }
    """
    llm = _create_postcard_llm()

    persona_name = {
        "standard": "Standart Seyahat Rehberi",
        "gourmet": "Gurme Şef",
        "history": "Tarih Profesörü",
        "budget": "Tasarrufçu Sırt Çantalı Gezgin"
    }.get(persona, "Standart Seyahat Rehberi")

    prompt_input = f"""
    Şehir: {city}
    Seyahat Karakteri (Persona): {persona_name}
    
    Seyahat Planı Özeti:
    {itinerary[:2000]}  # Token limitini korumak için planı sınırlıyoruz
    """

    messages = [
        SystemMessage(content=POSTCARD_SYSTEM_PROMPT),
        HumanMessage(content=prompt_input)
    ]

    response = llm.invoke(messages)
    response_text = response.content.strip()

    # JSON Çıktısını Ayrıştır
    postcard_data = _parse_postcard_json(response_text, city)

    # Pollinations.ai Görsel URL'sini oluştur
    encoded_prompt = urllib.parse.quote(postcard_data["image_prompt"])
    # Seed olarak 42 yerine dinamik veya sabit estetik bir seed kullanabiliriz.
    # Genişlik/Yükseklik oranını kartpostal formatına uygun olarak 800x500 yapıyoruz.
    postcard_data["image_url"] = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=500&nologo=true&seed=100"

    return postcard_data


def _parse_postcard_json(text: str, city: str) -> dict:
    """LLM yanıtından JSON verisini güvenli bir şekilde ayrıştırır."""
    # Doğrudan ayrıştırmayı dene
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Markdown kod bloklarını temizlemeyi dene (```json ... ```)
    clean_text = text
    if "```" in text:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            clean_text = match.group(1)
        else:
            # Sadece süslü parantezlerin arasını bulmaya çalış
            match_braces = re.search(r"(\{.*?\})", text, re.DOTALL)
            if match_braces:
                clean_text = match_braces.group(1)

    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        pass

    # Ayrıştırma tamamen başarısız olursa güvenli bir yedek (fallback) döndür
    return {
        "image_prompt": f"A beautiful vintage-style travel postcard illustration of {city}, warm sunset lighting, highly detailed art",
        "postcard_message": f"Sevgili Ailem, {city}'den harika seyahat selamları! Buradaki her an dolu dolu ve çok keyifli geçiyor. Yakında tüm detayları anlatmak için sabırsızlanıyorum. Hepinizi çok öpüyorum!"
    }
