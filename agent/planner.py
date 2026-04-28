"""
Planner Agent — ReAct pattern ile otonom seyahat planlama ajanı.
LangChain kullanarak weather ve scoring tool'larını dinamik olarak çağırır.
"""

import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent.prompts import PLANNER_SYSTEM_PROMPT
from tools.weather import get_weather
from tools.scoring import score_days

load_dotenv(override=True)


def _create_llm(temperature: float = 0.3) -> ChatGroq:
    """Groq LLM instance'ı oluşturur."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY ortam değişkeni bulunamadı. .env dosyasına ekleyin."
        )
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    return ChatGroq(
        model=model_name,
        groq_api_key=api_key,
        temperature=temperature,
        max_retries=3,
    )


def _create_agent_executor() -> AgentExecutor:
    """Tool calling agent ve executor oluşturur."""
    llm = _create_llm()
    tools = [get_weather, score_days]

    prompt = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
    )

    return executor


def run_planner_agent(
    city: str,
    start_date: str,
    end_date: str,
    preference: str = "both",
    persona: str = "standard",
) -> dict:
    """
    Planner agent'ı çalıştırır.

    Args:
        city: Şehir adı
        start_date: Başlangıç tarihi (YYYY-MM-DD)
        end_date: Bitiş tarihi (YYYY-MM-DD)
        preference: Kullanıcı tercihi ("outdoor", "indoor", "both")

    Returns:
        dict: {
            "output": Final itinerary text,
            "intermediate_steps": ReAct adımları,
            "weather_data": Ham hava durumu verisi,
            "scores": Skorlama sonuçları
        }
    """
    executor = _create_agent_executor()

    preference_text = {
        "outdoor": "Açık hava aktivitelerini tercih ediyorum.",
        "indoor": "Kapalı mekan aktivitelerini tercih ediyorum.",
        "both": "Hem açık hava hem kapalı mekan aktiviteleri olabilir.",
    }.get(preference, "Hem açık hava hem kapalı mekan aktiviteleri olabilir.")

    persona_text = {
        "standard": "Dengeli ve standart bir seyahat rehberi gibi davran.",
        "gourmet": "Sadece lezzet odaklı bir Gurme Şef gibi davran. Yöresel lezzetlere, Michelin yıldızlı yerlere veya meşhur sokak lezzetlerine odaklan. Klasik turistik yerlerden ziyade yemek kültürüne önem ver.",
        "history": "Bir Tarih Profesörü gibi davran. Şehrin tarihi dokusuna, antik kentlere, mimari yapılara ve müzelere odaklan. Hikayesi olan yerleri öner.",
        "budget": "Tasarrufçu bir Sırt Çantalı Gezgin (Backpacker) gibi davran. Ücretsiz veya çok ucuz aktivitelere, yürüyüş rotalarına, halk pazarlarına ve uygun fiyatlı yerel deneyimlere odaklan.",
    }.get(persona, "Dengeli ve standart bir seyahat rehberi gibi davran.")

    user_input = (
        f"Karakterin/Rolün: {persona_text}\n\n"
        f"{city} şehri için {start_date} ile {end_date} tarihleri arasında "
        f"seyahat planı oluştur. {preference_text} "
        f"Önce hava durumu verilerini al, sonra günleri skorla, "
        f"ve en iyi planı oluştur."
    )

    result = executor.invoke({"input": user_input})

    # Ara adımlardan weather ve score verilerini çıkar
    weather_data = None
    scores_data = None

    for step in result.get("intermediate_steps", []):
        action, observation = step
        if hasattr(action, "tool"):
            if action.tool == "get_weather":
                try:
                    weather_data = json.loads(observation)
                except (json.JSONDecodeError, TypeError):
                    weather_data = observation
            elif action.tool == "score_days":
                try:
                    scores_data = json.loads(observation)
                except (json.JSONDecodeError, TypeError):
                    scores_data = observation

    return {
        "output": result.get("output", ""),
        "intermediate_steps": result.get("intermediate_steps", []),
        "weather_data": weather_data,
        "scores": scores_data,
    }


def format_react_steps(intermediate_steps: list) -> list[dict]:
    """
    Ara adımları UI-friendly formata dönüştürür.

    Returns:
        list of dicts: [{"type": "thought"|"action"|"observation", "content": "..."}]
    """
    formatted = []

    for i, step in enumerate(intermediate_steps):
        action, observation = step

        # Thought (Action'dan önce agent'ın düşüncesi)
        if hasattr(action, "log") and action.log:
            thought_text = action.log.strip()
            if thought_text:
                formatted.append({
                    "type": "thought",
                    "step": i + 1,
                    "content": thought_text,
                })

        # Action
        tool_name = getattr(action, "tool", "unknown")
        tool_input = getattr(action, "tool_input", {})
        formatted.append({
            "type": "action",
            "step": i + 1,
            "content": f"🔧 Tool: {tool_name}",
            "tool_name": tool_name,
            "tool_input": tool_input,
        })

        # Observation
        obs_preview = str(observation)
        if len(obs_preview) > 500:
            obs_preview = obs_preview[:500] + "..."
        formatted.append({
            "type": "observation",
            "step": i + 1,
            "content": obs_preview,
        })

    return formatted
