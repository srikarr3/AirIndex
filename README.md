# 🌫️ AirIndex India — Production AQI Pipeline & Dashboard

A production-grade, real-time Air Quality Index (AQI) intelligence system and Streamlit dashboard monitoring Indian cities. Powered by official **Central Pollution Control Board (CPCB)** data from `data.gov.in`, **DuckDB**, **dbt core**, and **Apache Airflow / GitHub Actions**.

---

## 🏗️ Architecture & Data Pipeline Flow

```mermaid
flowchart TD
    subgraph Ingestion ["1. Data Ingestion"]
        CPCB["Govt CPCB API (data.gov.in)"] --> Ingest["src/ingest_cpcb.py"]
        Ingest --> DuckRaw["DuckDB: raw_aqi_readings"]
    end

    subgraph Transformation ["2. dbt Core Transformation Layer"]
        DuckRaw --> STG["dbt: stg_aqi_readings\n(CO Unit Normalization to mg/m³)"]
        STG --> INT["dbt: int_pollutant_subindex\n(CPCB Breakpoint Calculations)"]
        INT --> FactH["dbt: fact_city_aqi_hourly"]
        INT --> FactD["dbt: fact_city_aqi_daily"]
    end

    subgraph Intelligence ["3. Health & Advisory Layer"]
        FactH --> Advisory["src/genai_advisory.py"]
        Advisory --> DuckAdv["DuckDB: genai_advisories"]
    end

    subgraph Serving ["4. Presentation Layer"]
        FactH & DuckAdv & STG --> Streamlit["Modular Streamlit Dashboard (ui/)"]
    end
```

---

## ⚡ Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Create a `.env` file in the project root:
```env
DATA_GOV_IN_API_KEY=YOUR_API_KEY
```

### 3. Run End-to-End Pipeline & Launch App
```bash
# Run ingestion, station updates, dbt models, dbt tests & advisories
python run_pipeline.py

# Launch Streamlit web dashboard
streamlit run app.py
```


## 📖 Official CPCB AQI Breakpoint Matrix & Data Sources

### National Air Quality Index (NAQI) Breakpoints (Government of India)
Concentrations in µg/m³ (CO in mg/m³):

| Category | Index Range | PM₂.₅ (24h) | PM₁₀ (24h) | NO₂ (24h) | SO₂ (24h) | CO (8h) | O₃ (8h) | NH₃ (24h) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Good** | 0–50 | 0–30 | 0–50 | 0–40 | 0–40 | 0–1.0 | 0–50 | 0–200 |
| **Satisfactory** | 51–100 | 31–60 | 51–100 | 41–80 | 41–80 | 1.1–2.0 | 51–100 | 201–400 |
| **Moderate** | 101–200 | 61–90 | 101–250 | 81–180 | 81–380 | 2.1–10.0 | 101–168 | 401–800 |
| **Poor** | 201–300 | 91–120 | 251–350 | 181–280 | 381–800 | 10.1–17.0 | 169–208 | 801–1200 |
| **Very Poor** | 301–400 | 121–250 | 351–430 | 281–400 | 801–1600 | 17.1–34.0 | 209–748 | 1201–1800 |
| **Severe** | 401–500 | >250 | >430 | >400 | >1600 | >34.0 | >748 | >1800 |

### Official Data Source References
- **Data Provider**: Central Pollution Control Board (CPCB), Ministry of Environment, Forest and Climate Change, Govt. of India.
- **Open Data Portal**: [data.gov.in — Real-time Air Quality Index API](https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69)

---

## 📁 Repository Modular Structure

```
airindex/
├── .github/workflows/
├── app.py
├── config.py
├── dags/
├── dbt_airindex/
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
├── run_pipeline.py
├── src/
│   ├── db.py
│   ├── genai_advisory.py
│   ├── ingest_cpcb.py
│   └── seed_loader.py
└── ui/
    ├── components/
    ├── data.py
    ├── icons.py
    └── theme.py
```
