{{ config(materialized='view') }}

WITH stg AS (
    SELECT * FROM {{ ref('stg_aqi_readings') }}
),

normalized_stg AS (
    SELECT
        id,
        country,
        state,
        city,
        station,
        pollutant_id,
        avg_value,
        avg_value AS norm_avg_value,
        last_update,
        DATE_TRUNC('hour', last_update) AS hour_ts
    FROM stg
),

calculated_subindex AS (
    SELECT
        id,
        country,
        state,
        city,
        station,
        pollutant_id,
        avg_value,
        norm_avg_value,
        last_update,
        hour_ts,
        CAST(
            CASE
                -- 1. PM2.5 (24h avg ug/m3)
                WHEN pollutant_id IN ('PM2.5', 'PM25') THEN
                    CASE
                        WHEN norm_avg_value <= 30 THEN norm_avg_value * (50.0 / 30.0)
                        WHEN norm_avg_value <= 60 THEN 51.0 + (norm_avg_value - 30.0) * (49.0 / 30.0)
                        WHEN norm_avg_value <= 90 THEN 101.0 + (norm_avg_value - 60.0) * (99.0 / 30.0)
                        WHEN norm_avg_value <= 120 THEN 201.0 + (norm_avg_value - 90.0) * (99.0 / 30.0)
                        WHEN norm_avg_value <= 250 THEN 301.0 + (norm_avg_value - 120.0) * (99.0 / 130.0)
                        ELSE 401.0 + (norm_avg_value - 250.0) * (99.0 / 130.0)
                    END

                -- 2. PM10 (24h avg ug/m3)
                WHEN pollutant_id = 'PM10' THEN
                    CASE
                        WHEN norm_avg_value <= 50 THEN norm_avg_value * (50.0 / 50.0)
                        WHEN norm_avg_value <= 100 THEN 51.0 + (norm_avg_value - 50.0) * (49.0 / 50.0)
                        WHEN norm_avg_value <= 250 THEN 101.0 + (norm_avg_value - 100.0) * (99.0 / 150.0)
                        WHEN norm_avg_value <= 350 THEN 201.0 + (norm_avg_value - 250.0) * (99.0 / 100.0)
                        WHEN norm_avg_value <= 430 THEN 301.0 + (norm_avg_value - 350.0) * (99.0 / 80.0)
                        ELSE 401.0 + (norm_avg_value - 430.0) * (99.0 / 80.0)
                    END

                -- 3. NO2 (24h avg ug/m3)
                WHEN pollutant_id = 'NO2' THEN
                    CASE
                        WHEN norm_avg_value <= 40 THEN norm_avg_value * (50.0 / 40.0)
                        WHEN norm_avg_value <= 80 THEN 51.0 + (norm_avg_value - 40.0) * (49.0 / 40.0)
                        WHEN norm_avg_value <= 180 THEN 101.0 + (norm_avg_value - 80.0) * (99.0 / 100.0)
                        WHEN norm_avg_value <= 280 THEN 201.0 + (norm_avg_value - 180.0) * (99.0 / 100.0)
                        WHEN norm_avg_value <= 400 THEN 301.0 + (norm_avg_value - 280.0) * (99.0 / 120.0)
                        ELSE 401.0 + (norm_avg_value - 400.0) * (99.0 / 100.0)
                    END

                -- 4. SO2 (24h avg ug/m3)
                WHEN pollutant_id = 'SO2' THEN
                    CASE
                        WHEN norm_avg_value <= 40 THEN norm_avg_value * (50.0 / 40.0)
                        WHEN norm_avg_value <= 80 THEN 51.0 + (norm_avg_value - 40.0) * (49.0 / 40.0)
                        WHEN norm_avg_value <= 380 THEN 101.0 + (norm_avg_value - 80.0) * (99.0 / 300.0)
                        WHEN norm_avg_value <= 800 THEN 201.0 + (norm_avg_value - 380.0) * (99.0 / 420.0)
                        WHEN norm_avg_value <= 1600 THEN 301.0 + (norm_avg_value - 800.0) * (99.0 / 800.0)
                        ELSE 401.0 + (norm_avg_value - 1600.0) * (99.0 / 800.0)
                    END

                -- 5. CO (8h avg mg/m3)
                WHEN pollutant_id = 'CO' THEN
                    CASE
                        WHEN norm_avg_value <= 1.0 THEN norm_avg_value * (50.0 / 1.0)
                        WHEN norm_avg_value <= 2.0 THEN 51.0 + (norm_avg_value - 1.0) * (49.0 / 1.0)
                        WHEN norm_avg_value <= 10.0 THEN 101.0 + (norm_avg_value - 2.0) * (99.0 / 8.0)
                        WHEN norm_avg_value <= 17.0 THEN 201.0 + (norm_avg_value - 10.0) * (99.0 / 7.0)
                        WHEN norm_avg_value <= 34.0 THEN 301.0 + (norm_avg_value - 17.0) * (99.0 / 17.0)
                        ELSE 401.0 + (norm_avg_value - 34.0) * (99.0 / 17.0)
                    END

                -- 6. O3 (8h avg ug/m3)
                WHEN pollutant_id IN ('O3', 'OZONE') THEN
                    CASE
                        WHEN norm_avg_value <= 50 THEN norm_avg_value * (50.0 / 50.0)
                        WHEN norm_avg_value <= 100 THEN 51.0 + (norm_avg_value - 50.0) * (49.0 / 50.0)
                        WHEN norm_avg_value <= 168 THEN 101.0 + (norm_avg_value - 100.0) * (99.0 / 68.0)
                        WHEN norm_avg_value <= 208 THEN 201.0 + (norm_avg_value - 168.0) * (99.0 / 40.0)
                        WHEN norm_avg_value <= 748 THEN 301.0 + (norm_avg_value - 208.0) * (99.0 / 540.0)
                        ELSE 401.0 + (norm_avg_value - 748.0) * (99.0 / 252.0)
                    END

                -- 7. NH3 (24h avg ug/m3)
                WHEN pollutant_id = 'NH3' THEN
                    CASE
                        WHEN norm_avg_value <= 200 THEN norm_avg_value * (50.0 / 200.0)
                        WHEN norm_avg_value <= 400 THEN 51.0 + (norm_avg_value - 200.0) * (49.0 / 200.0)
                        WHEN norm_avg_value <= 800 THEN 101.0 + (norm_avg_value - 400.0) * (99.0 / 400.0)
                        WHEN norm_avg_value <= 1200 THEN 201.0 + (norm_avg_value - 800.0) * (99.0 / 400.0)
                        WHEN norm_avg_value <= 1800 THEN 301.0 + (norm_avg_value - 1200.0) * (99.0 / 600.0)
                        ELSE 401.0 + (norm_avg_value - 1800.0) * (99.0 / 600.0)
                    END

                -- 8. Pb (24h avg ug/m3)
                WHEN pollutant_id IN ('PB', 'LEAD') THEN
                    CASE
                        WHEN norm_avg_value <= 0.5 THEN norm_avg_value * (50.0 / 0.5)
                        WHEN norm_avg_value <= 1.0 THEN 51.0 + (norm_avg_value - 0.5) * (49.0 / 0.5)
                        WHEN norm_avg_value <= 2.0 THEN 101.0 + (norm_avg_value - 1.0) * (99.0 / 1.0)
                        WHEN norm_avg_value <= 3.0 THEN 201.0 + (norm_avg_value - 2.0) * (99.0 / 1.0)
                        WHEN norm_avg_value <= 3.5 THEN 301.0 + (norm_avg_value - 3.0) * (99.0 / 0.5)
                        ELSE 401.0 + (norm_avg_value - 3.5) * (99.0 / 0.5)
                    END
                ELSE NULL
            END AS INTEGER
        ) AS subindex
    FROM normalized_stg
)

SELECT
    id,
    country,
    state,
    city,
    station,
    pollutant_id,
    avg_value,
    last_update,
    hour_ts,
    LEAST(GREATEST(subindex, 0), 500) AS subindex
FROM calculated_subindex
WHERE subindex IS NOT NULL
