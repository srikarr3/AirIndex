{{ config(materialized='table') }}

WITH subindex_data AS (
    SELECT * FROM {{ ref('int_pollutant_subindex') }}
),

ranked_pollutants AS (
    SELECT
        city,
        hour_ts,
        pollutant_id,
        subindex,
        COUNT(DISTINCT station) OVER(PARTITION BY city, hour_ts) AS station_count,
        MAX(subindex) OVER(PARTITION BY city, hour_ts) AS max_subindex,
        ROW_NUMBER() OVER(
            PARTITION BY city, hour_ts 
            ORDER BY subindex DESC, pollutant_id ASC
        ) as rn
    FROM subindex_data
),

hourly_aggregated AS (
    SELECT
        city,
        hour_ts,
        max_subindex AS overall_aqi,
        pollutant_id AS dominant_pollutant,
        station_count,
        CASE
            WHEN max_subindex <= 50 THEN 'Good'
            WHEN max_subindex <= 100 THEN 'Satisfactory'
            WHEN max_subindex <= 200 THEN 'Moderate'
            WHEN max_subindex <= 300 THEN 'Poor'
            WHEN max_subindex <= 400 THEN 'Very Poor'
            ELSE 'Severe'
        END AS category
    FROM ranked_pollutants
    WHERE rn = 1
)

SELECT
    city,
    hour_ts,
    overall_aqi,
    dominant_pollutant,
    category,
    station_count
FROM hourly_aggregated
