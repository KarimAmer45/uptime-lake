-- Quantified results for README and interview evidence.
SELECT 'bronze' AS layer, count(*) AS rows FROM metro.bronze.sensor_readings_raw
UNION ALL
SELECT 'silver', count(*) FROM metro.silver.sensor_readings
UNION ALL
SELECT 'rejects', count(*) FROM metro.silver.sensor_readings_rejects
UNION ALL
SELECT 'gold_fact', count(*) FROM metro.gold.fact_sensor_reading;

SELECT check_name, checked_rows, failed_rows,
       round((checked_rows - failed_rows) / checked_rows * 100, 4) AS pass_rate_pct
FROM metro.audit.quality_check_results
QUALIFY row_number() OVER (PARTITION BY check_name ORDER BY checked_at DESC) = 1
ORDER BY check_name;

SELECT *
FROM metro.audit.pipeline_validation_results
QUALIFY row_number() OVER (PARTITION BY check_name ORDER BY checked_at DESC) = 1
ORDER BY check_name;

SELECT calendar_date, telemetry_coverage_pct, anomaly_rate_pct,
       avg_oil_temperature_c, max_motor_current_a, known_failure_window_readings
FROM metro.gold.powerbi_equipment_health
ORDER BY calendar_date;

