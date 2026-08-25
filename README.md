# AirIndex India — AQI Pipeline & Dashboard

Real-time Air Quality Index (AQI) pipeline and Streamlit dashboard for Indian cities, powered by CPCB data from `data.gov.in`, DuckDB, and dbt.

## 🚀 Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Create a `.env` file in the project root:
```env
DATA_GOV_IN_API_KEY=YOUR_API_KEY
```

### 3. Run Pipeline & Dashboard
```bash
# Run data pipeline CLI
python run_pipeline.py

# Launch Streamlit dashboard
streamlit run app.py
```

## ☁️ Deployment (Streamlit Cloud)

1. Push code to your GitHub repository.
2. Connect your repository on [share.streamlit.io](https://share.streamlit.io/).
3. Set **Main file path** to `app.py`.
4. In **Advanced Settings -> Secrets**, add:
   ```toml
   DATA_GOV_IN_API_KEY = "YOUR_API_KEY"
   ```
5. Click **Deploy**!
