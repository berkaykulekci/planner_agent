"""
Local Lingo Generator — Seyahat edilen şehrin yerel dil rehberini hazırlar.
"""

import os
import re
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from agent.prompts import LINGO_SYSTEM_PROMPT

load_dotenv(override=True)


def _create_lingo_llm() -> ChatGroq:
    """Dil rehberi üretimi için LLM oluşturur."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY ortam değişkeni bulunamadı. .env dosyasına ekleyin.")

    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        groq_api_key=api_key,
        temperature=0.4,  # Daha yapılandırılmış ve kararlı çeviriler için orta sıcaklık
        max_retries=3,
    )


def generate_local_lingo(city: str, persona: str) -> dict:
    """
    Seyahat edilen şehre ve karaktere özel yerel dil kalıpları üretir.

    Args:
        city: Şehir adı
        persona: Seyahat karakteri

    Returns:
        dict: {
            "language": "Fransızca",
            "phrases": [
                {"phrase": "...", "pronunciation": "...", "meaning": "...", "context": "..."},
                ...
            ]
        }
    """
    llm = _create_lingo_llm()

    persona_name = {
        "standard": "Standart Seyahat Rehberi",
        "gourmet": "Gurme Şef",
        "history": "Tarih Profesörü",
        "budget": "Tasarrufçu Sırt Çantalı Gezgin"
    }.get(persona, "Standart Seyahat Rehberi")

    prompt_input = f"""
    Şehir: {city}
    Seyahat Karakteri (Persona): {persona_name}
    """

    messages = [
        SystemMessage(content=LINGO_SYSTEM_PROMPT),
        HumanMessage(content=prompt_input)
    ]

    response = llm.invoke(messages)
    response_text = response.content.strip()

    # JSON Çıktısını Ayrıştır
    return _parse_lingo_json(response_text, city)


def _parse_lingo_json(text: str, city: str) -> dict:
    """LLM yanıtından dil JSON verisini güvenli bir şekilde ayrıştırır."""
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
        "language": "Yerel Dil",
        "phrases": [
            {
                "phrase": "Hello / Good morning",
                "pronunciation": "Helo / Gud morning",
                "meaning": "Merhaba / Günaydın",
                "context": "Yerel halkla iletişim kurarken güler yüzle selam vermek her zaman en iyi başlangıçtır."
            },
            {
                "phrase": "Thank you",
                "pronunciation": "Tenk yu",
                "meaning": "Teşekkür ederim",
                "context": "Size yardımcı olan herkese nezaketen teşekkür etmeyi unutmayın."
            },
            {
                "phrase": "Where is...?",
                "pronunciation": "Ver iz...?",
                "meaning": "... nerede?",
                "context": "Gitmek istediğiniz popüler noktaları veya tarihi yapıları sormak için kullanabilirsiniz."
            },
            {
                "phrase": "How much is this?",
                "pronunciation": "Hav maç iz diz?",
                "meaning": "Bu ne kadar?",
                "context": "Alışveriş yaparken veya yerel pazarlarda fiyat sormak için kullanılır."
            },
            {
                "phrase": "Goodbye",
                "pronunciation": "Gudbay",
                "meaning": "Hoşça kalın",
                "context": "Bir dükkandan veya restorandan ayrılırken kullanabileceğiniz kibar veda sözü."
            }
        ]
    }
