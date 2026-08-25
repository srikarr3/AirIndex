{{ config(materialized='table') }}

WITH hourly AS (
    SELECT * FROM {{ ref('fact_city_aqi_hourly') }}
),

daily_stats AS (
    SELECT
        city,
        CAST(hour_ts AS DATE) AS date,
        CAST(ROUND(AVG(overall_aqi)) AS INTEGER) AS avg_aqi,
        MIN(overall_aqi) AS min_aqi,
        MAX(overall_aqi) AS max_aqi,
        MAX(station_count) AS max_station_count
    FROM hourly
    GROUP BY city, CAST(hour_ts AS DATE)
),

dominant_counts AS (
    SELECT
        city,
        CAST(hour_ts AS DATE) AS date,
        dominant_pollutant,
        COUNT(*) as cnt,
        ROW_NUMBER() OVER(PARTITION BY city, CAST(hour_ts AS DATE) ORDER BY COUNT(*) DESC) as rn
    FROM hourly
    GROUP BY city, CAST(hour_ts AS DATE), dominant_pollutant
)

SELECT
    s.city,
    s.date,
    s.avg_aqi,
    s.min_aqi,
    s.max_aqi,
    d.dominant_pollutant,
    CASE
        WHEN s.avg_aqi <= 50 THEN 'Good'
        WHEN s.avg_aqi <= 100 THEN 'Satisfactory'
        WHEN s.avg_aqi <= 200 THEN 'Moderate'
        WHEN s.avg_aqi <= 300 THEN 'Poor'
        WHEN s.avg_aqi <= 400 THEN 'Very Poor'
        ELSE 'Severe'
    END AS category,
    s.max_station_count AS station_count
FROM daily_stats s
JOIN dominant_counts d
  ON s.city = d.city 
 AND s.date = d.date 
 AND d.rn = 1
