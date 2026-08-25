{{ config(materialized='view') }}

WITH source_data AS (
    SELECT
        id,
        TRIM(country) AS country,
        TRIM(state) AS state,
        CASE 
            WHEN LOWER(TRIM(city)) IN ('bangalore', 'bengaluru') THEN 'Bengaluru'
            WHEN LOWER(TRIM(city)) IN ('delhi', 'new delhi') THEN 'Delhi'
            WHEN LOWER(TRIM(city)) = 'mumbai' THEN 'Mumbai'
            WHEN LOWER(TRIM(city)) = 'chennai' THEN 'Chennai'
            WHEN LOWER(TRIM(city)) = 'kolkata' THEN 'Kolkata'
            WHEN LOWER(TRIM(city)) = 'hyderabad' THEN 'Hyderabad'
            WHEN LOWER(TRIM(city)) = 'pune' THEN 'Pune'
            WHEN LOWER(TRIM(city)) = 'ahmedabad' THEN 'Ahmedabad'
            ELSE UPPER(SUBSTR(TRIM(city), 1, 1)) || LOWER(SUBSTR(TRIM(city), 2))
        END AS city,
        TRIM(station) AS station,
        UPPER(TRIM(pollutant_id)) AS pollutant_id,
        CAST(min_value AS DOUBLE) AS min_value,
        CAST(max_value AS DOUBLE) AS max_value,
        CAST(avg_value AS DOUBLE) AS avg_value,
        CAST(latitude AS DOUBLE) AS latitude,
        CAST(longitude AS DOUBLE) AS longitude,
        CAST(last_update AS TIMESTAMP) AS last_update,
        CAST(ingested_at AS TIMESTAMP) AS ingested_at
    FROM {{ source('main', 'raw_aqi_readings') }}
)

SELECT *
FROM source_data
WHERE avg_value IS NOT NULL
  AND last_update IS NOT NULL
  AND city IS NOT NULL AND city != ''
  AND station IS NOT NULL AND station != ''
  AND pollutant_id IS NOT NULL AND pollutant_id != ''
