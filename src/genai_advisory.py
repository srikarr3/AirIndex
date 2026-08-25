import os
from datetime import datetime
import duckdb
from config import DUCKDB_PATH
from src.db import get_db_connection

def generate_advisory_for_row(city: str, date_str: str, avg_aqi: int, min_aqi: int, max_aqi: int, dominant_pollutant: str, category: str):
    """
    Generates a 2-3 sentence public health advisory based strictly on ingested daily AQI facts.
    Uses Gemini API if GEMINI_API_KEY is present, otherwise produces a grounded deterministic advisory.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    prompt = (
        f"You are an expert environmental health advisor. Write a concise 2-3 sentence public health advisory for {city} on {date_str}. "
        f"The day's average AQI was {avg_aqi} (Min: {min_aqi}, Max: {max_aqi}), placing it in the '{category}' category, "
        f"with {dominant_pollutant} as the dominant pollutant. "
        "Explain what the air quality was like, who should take extra caution (general public vs sensitive groups), and one practical health tip. "
        "Do not invent any additional facts or metrics."
    )

    if gemini_key and gemini_key != "your_gemini_api_key_here":
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"Gemini API call failed for {city}: {e}. Falling back to rule-based advisory.")

    # Grounded fallback advisory strictly based on ingested numbers
    caution_groups = {
        "Good": "the general public can enjoy normal outdoor activities with clean air quality.",
        "Satisfactory": "sensitive individuals with severe allergies should monitor mild symptoms during prolonged exposure.",
        "Moderate": "children, the elderly, and individuals with respiratory condition like asthma should limit prolonged heavy exertion outdoors.",
        "Poor": "sensitive groups should avoid outdoor exertion, while the general public should reduce strenuous outdoor activities.",
        "Very Poor": "everyone should avoid prolonged outdoor activities and wear protective N95 masks when stepping out.",
        "Severe": "all individuals must stay indoors, use air purifiers, and keep windows closed due to hazardous air pollution levels."
    }
    
    advice = caution_groups.get(category, "residents should exercise caution outdoors.")
    
    fallback_text = (
        f"In {city} on {date_str}, air quality registered an average AQI of {avg_aqi} ({category} category), "
        f"reaching a peak of {max_aqi} with {dominant_pollutant} as the dominant pollutant. "
        f"For health protection, {advice}"
    )
    return fallback_text

def run_genai_advisories(db_path: str = DUCKDB_PATH):
    """
    Scans fact_city_aqi_daily for records missing an advisory in genai_advisories table
    and generates/stores clean advisories.
    """
    conn = get_db_connection(db_path)
    
    # Check if fact_city_aqi_daily exists
    table_exists = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'fact_city_aqi_daily'"
    ).fetchone()[0]
    
    if not table_exists:
        print("fact_city_aqi_daily table does not exist yet. Run dbt models first.")
        conn.close()
        return 0

    rows = conn.execute("""
        SELECT 
            d.city,
            CAST(d.date AS TEXT) AS date_str,
            d.avg_aqi,
            d.min_aqi,
            d.max_aqi,
            d.dominant_pollutant,
            d.category
        FROM fact_city_aqi_daily d
        LEFT JOIN genai_advisories a ON d.city = a.city AND d.date = a.date
        WHERE a.advisory_text IS NULL
    """).fetchall()

    if not rows:
        print("No new city days pending health advisory generation.")
        conn.close()
        return 0

    generated_count = 0
    now_ts = datetime.now()

    print(f"Generating health advisories for {len(rows)} city-day records...")
    for r in rows:
        city, date_str, avg_aqi, min_aqi, max_aqi, dominant_pollutant, category = r
        advisory_text = generate_advisory_for_row(
            city=city,
            date_str=date_str,
            avg_aqi=avg_aqi,
            min_aqi=min_aqi,
            max_aqi=max_aqi,
            dominant_pollutant=dominant_pollutant,
            category=category
        )
        
        conn.execute("""
            INSERT INTO genai_advisories (city, date, advisory_text, generated_at)
            VALUES (?, CAST(? AS DATE), ?, ?)
            ON CONFLICT (city, date) DO UPDATE SET
                advisory_text = EXCLUDED.advisory_text,
                generated_at = EXCLUDED.generated_at;
        """, (city, date_str, advisory_text, now_ts))
        generated_count += 1
        print(f"  -> Generated advisory for {city} ({date_str})")

    conn.close()
    print(f"Completed GenAI advisory generation. Total generated: {generated_count}")
    return generated_count

if __name__ == "__main__":
    run_genai_advisories()
