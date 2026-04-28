"""
Agentic AI Travel Planner — CLI Entry Point
Komut satırından agent'ı çalıştırmak için kullanılır.
"""

import sys
import json
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

from agent.planner import run_planner_agent, format_react_steps
from evaluation.evaluator import evaluate_itinerary
from agent.memory import save_search


def main():
    print("=" * 60)
    print("  ✈️  Agentic AI Travel Planner — CLI Mode")
    print("=" * 60)

    # Kullanıcıdan input al
    city = input("\n🏙️  Şehir adı (örn: Istanbul): ").strip() or "Istanbul"

    today = datetime.now().date()
    default_start = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    default_end = (today + timedelta(days=4)).strftime("%Y-%m-%d")

    start_date = input(f"📅 Başlangıç tarihi ({default_start}): ").strip() or default_start
    end_date = input(f"📅 Bitiş tarihi ({default_end}): ").strip() or default_end

    print("\nAktivite tercihi:")
    print("  1. Her İkisi (outdoor + indoor)")
    print("  2. Açık Hava (outdoor)")
    print("  3. Kapalı Mekan (indoor)")
    pref_choice = input("Seçiminiz (1/2/3, varsayılan: 1): ").strip() or "1"
    preference = {"1": "both", "2": "outdoor", "3": "indoor"}.get(pref_choice, "both")

    # Aramayı kaydet
    save_search(city, start_date, end_date, preference)

    print("\n" + "─" * 60)
    print("🤖 Agent çalıştırılıyor...")
    print("─" * 60)

    # Agent'ı çalıştır
    try:
        result = run_planner_agent(
            city=city,
            start_date=start_date,
            end_date=end_date,
            preference=preference,
        )
    except Exception as e:
        print(f"\n❌ Agent hatası: {e}")
        sys.exit(1)

    # ReAct adımlarını göster
    print("\n" + "─" * 60)
    print("🧠 ReAct Adımları:")
    print("─" * 60)

    steps = format_react_steps(result.get("intermediate_steps", []))
    for step in steps:
        if step["type"] == "thought":
            print(f"\n💭 [Thought] {step['content']}")
        elif step["type"] == "action":
            print(f"⚡ [Action] {step['content']}")
        elif step["type"] == "observation":
            content = step["content"]
            if len(content) > 300:
                content = content[:300] + "..."
            print(f"👁️ [Observation] {content}")

    # Final plan
    print("\n" + "=" * 60)
    print("📝 SEYAHAT PLANI")
    print("=" * 60)
    print(result["output"])

    # Evaluation
    print("\n" + "─" * 60)
    print("🔍 Değerlendirme Ajanı çalışıyor...")
    print("─" * 60)

    try:
        eval_result = evaluate_itinerary(
            weather_data=result.get("weather_data"),
            scores_data=result.get("scores"),
            itinerary=result["output"],
            city=city,
        )
        print(f"\n🏆 Değerlendirme Skoru: {eval_result['score']}/10")
        print("\n" + eval_result["evaluation_text"])
    except Exception as e:
        print(f"\n⚠️ Değerlendirme hatası: {e}")

    print("\n" + "=" * 60)
    print("✅ Tamamlandı!")
    print("=" * 60)


if __name__ == "__main__":
    main()
