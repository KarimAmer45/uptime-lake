"""Production transformations for the Databricks job notebooks."""

from __future__ import annotations

from uptime_lake.config import PipelineConfig
from uptime_lake.contracts import SOURCE_COLUMNS
from uptime_lake.quality import apply_quality_gate, quality_summary, split_quality_rows

# UCI ships MetroPT-3 with a leading, unnamed pandas index column. Different
# CSV exports label it differently, so normalise any of these to `index`.
_UNNAMED_INDEX_ALIASES = ("", "_c0", "Unnamed: 0")


def setup_catalog(spark, config: PipelineConfig, read_principal: str = "") -> None:
    spark.sql(f"CREATE CATALOG IF NOT EXISTS `{config.catalog}` COMMENT 'MetroPT-3 IoT lakehouse'")
    for schema, comment in (
        (config.bronze_schema, "Auditable raw IoT readings"),
        (config.silver_schema, "Typed, deduplicated and validated IoT readings"),
        (config.gold_schema, "Business-ready equipment health facts and dimensions"),
        (config.audit_schema, "Pipeline quality and validation evidence"),
    ):
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{config.catalog}`.`{schema}` COMMENT '{comment}'")
    if read_principal:
        escaped = read_principal.replace("`", "``")
        spark.sql(f"GRANT USE CATALOG ON CATALOG `{config.catalog}` TO `{escaped}`")
        spark.sql(f"GRANT USE SCHEMA ON SCHEMA `{config.catalog}`.`{config.gold_schema}` TO `{escaped}`")
        spark.sql(f"GRANT SELECT ON SCHEMA `{config.catalog}`.`{config.gold_schema}` TO `{escaped}`")


def ingest_bronze(spark, config: PipelineConfig, source_path: str, run_id: str) -> int:
    from pyspark.sql import functions as F

    if not source_path.strip():
        raise ValueError("source_path must be an ADLS abfss:// path or a Unity Catalog volume path")
    # Read every field as a string by name; Bronze preserves the raw copy as-is and the
    # Silver contract does the typing. Selecting by name avoids the positional mislabelling
    # that a fixed .schema() suffers when the file column order or count drifts.
    frame = (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "false")
        .option("multiLine", "false")
        .load(source_path)
    )
    first_column = frame.columns[0]
    if first_column in _UNNAMED_INDEX_ALIASES and "index" not in frame.columns:
        frame = frame.withColumnRenamed(first_column, "index")
    missing = sorted(set(SOURCE_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Source is missing required columns: {missing}")
    bronze = frame.select(*SOURCE_COLUMNS).withColumns(
        {
            "_source_file": F.input_file_name(),
            "_ingested_at": F.current_timestamp(),
            "_run_id": F.lit(str(run_id)),
        }
    )
    table = config.table("bronze", "sensor_readings_raw")
    bronze.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(table)
    spark.sql(f"COMMENT ON TABLE {table} IS 'Raw MetroPT-3 readings preserved as received from ADLS'")
    return spark.table(table).count()


def build_silver(spark, config: PipelineConfig, run_id: str) -> tuple[int, int]:
    bronze_table = config.table("bronze", "sensor_readings_raw")
    silver_table = config.table("silver", "sensor_readings")
    rejects_table = config.table("silver", "sensor_readings_rejects")
    summary_table = config.table("audit", "quality_check_results")

    quality_frame = apply_quality_gate(spark.table(bronze_table), config.equipment_id).cache()
    valid, rejects = split_quality_rows(quality_frame)
    valid.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(silver_table)
    rejects.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(rejects_table)
    quality_summary(spark, quality_frame, run_id).write.format("delta").mode("append").saveAsTable(summary_table)
    valid_count = spark.table(silver_table).count()
    reject_count = spark.table(rejects_table).count()
    quality_frame.unpersist()

    spark.sql(f"COMMENT ON TABLE {silver_table} IS 'Typed, deduplicated MetroPT-3 readings that passed 10 quality rules'")
    spark.sql(f"COMMENT ON TABLE {rejects_table} IS 'Rejected readings with one or more explicit rejection reasons'")
    spark.sql(f"COMMENT ON COLUMN {rejects_table}.rejection_reason IS 'Semicolon-delimited failed quality rule names'")
    return valid_count, reject_count


def build_gold(spark, config: PipelineConfig) -> None:
    silver = config.table("silver", "sensor_readings")
    equipment = config.table("gold", "dim_equipment")
    dates = config.table("gold", "dim_date")
    failures = config.table("gold", "dim_failure_event")
    fact = config.table("gold", "fact_sensor_reading")
    daily = config.table("gold", "fact_daily_equipment_health")
    dashboard = config.table("gold", "powerbi_equipment_health")

    spark.sql(f"""
        CREATE OR REPLACE TABLE {equipment} USING DELTA
        COMMENT 'Equipment dimension for the Porto metro Air Production Unit'
        AS SELECT '{config.equipment_id}' AS equipment_id,
                  'Metro train Air Production Unit' AS equipment_name,
                  'compressor' AS equipment_type,
                  'Porto Metro, Portugal' AS operating_context
    """)
    spark.sql(f"""
        CREATE OR REPLACE TABLE {dates} USING DELTA
        COMMENT 'Calendar dimension derived from accepted readings'
        AS SELECT DISTINCT
          CAST(date_format(event_ts, 'yyyyMMdd') AS INT) AS date_key,
          CAST(event_ts AS DATE) AS calendar_date,
          year(event_ts) AS year,
          quarter(event_ts) AS quarter,
          month(event_ts) AS month,
          date_format(event_ts, 'MMMM') AS month_name,
          weekofyear(event_ts) AS week_of_year,
          dayofmonth(event_ts) AS day_of_month,
          dayofweek(event_ts) AS day_of_week,
          date_format(event_ts, 'EEEE') AS day_name,
          CASE WHEN dayofweek(event_ts) IN (1, 7) THEN true ELSE false END AS is_weekend
        FROM {silver}
    """)
    spark.sql(f"""
        CREATE OR REPLACE TABLE {failures} USING DELTA
        COMMENT 'Known failure intervals published with MetroPT-3'
        AS SELECT * FROM VALUES
          (1, TIMESTAMP'2020-04-18 00:00:00', TIMESTAMP'2020-04-18 23:59:59', 'Air leak', 'High stress', NULL),
          (2, TIMESTAMP'2020-05-29 23:30:00', TIMESTAMP'2020-05-30 06:00:00', 'Air leak', 'High stress', 'Maintenance reported 2020-05-30'),
          (3, TIMESTAMP'2020-06-05 10:00:00', TIMESTAMP'2020-06-07 14:30:00', 'Air leak', 'High stress', 'Maintenance 2020-06-08 16:00'),
          (4, TIMESTAMP'2020-07-15 14:30:00', TIMESTAMP'2020-07-15 19:00:00', 'Air leak', 'High stress', 'Maintenance 2020-07-16 00:00')
        AS t(failure_event_id, start_ts, end_ts, failure_type, severity, notes)
    """)
    spark.sql(f"""
        CREATE OR REPLACE TABLE {fact} USING DELTA
        CLUSTER BY (date_key)
        COMMENT 'Reading-grain equipment health fact with explainable anomaly flags'
        AS SELECT
          s.reading_id,
          s.equipment_id,
          s.event_ts,
          CAST(date_format(s.event_ts, 'yyyyMMdd') AS INT) AS date_key,
          CAST(date_format(s.event_ts, 'HHmmss') AS INT) AS time_key,
          s.tp2, s.tp3, s.h1, s.dv_pressure, s.reservoirs,
          s.oil_temperature, s.motor_current, s.comp, s.dv_electric,
          s.towers, s.mpg, s.lps, s.pressure_switch, s.oil_level, s.caudal_impulses,
          (SELECT min(f.failure_event_id) FROM {failures} f
             WHERE s.event_ts BETWEEN f.start_ts AND f.end_ts) AS failure_event_id,
          concat_ws('; ',
            CASE WHEN s.oil_temperature > 100 THEN 'high_oil_temperature' END,
            CASE WHEN s.motor_current > 12 THEN 'high_motor_current' END,
            CASE WHEN abs(s.tp3 - s.reservoirs) > 1.5 THEN 'reservoir_pressure_mismatch' END,
            CASE WHEN s.lps = 1 THEN 'low_pressure_switch_active' END,
            CASE WHEN s.oil_level = 1 THEN 'low_oil_level_signal' END
          ) AS anomaly_reason
        FROM {silver} s
    """)
    spark.sql(f"""
        CREATE OR REPLACE TABLE {daily} USING DELTA
        CLUSTER BY (date_key)
        COMMENT 'Daily KPI fact consumed by Power BI'
        AS SELECT
          equipment_id,
          date_key,
          count(*) AS reading_count,
          round(least(count(*) / 8640.0, 1.0) * 100, 2) AS telemetry_coverage_pct,
          sum(CASE WHEN anomaly_reason <> '' THEN 1 ELSE 0 END) AS anomaly_reading_count,
          round(avg(CASE WHEN anomaly_reason <> '' THEN 1.0 ELSE 0.0 END) * 100, 3) AS anomaly_rate_pct,
          sum(CASE WHEN failure_event_id IS NOT NULL THEN 1 ELSE 0 END) AS known_failure_window_readings,
          round(avg(tp2), 4) AS avg_tp2_bar,
          round(avg(tp3), 4) AS avg_tp3_bar,
          round(avg(reservoirs), 4) AS avg_reservoirs_bar,
          round(avg(oil_temperature), 3) AS avg_oil_temperature_c,
          round(max(oil_temperature), 3) AS max_oil_temperature_c,
          round(avg(motor_current), 3) AS avg_motor_current_a,
          round(max(motor_current), 3) AS max_motor_current_a
        FROM {fact}
        GROUP BY equipment_id, date_key
    """)
    spark.sql(f"""
        CREATE OR REPLACE VIEW {dashboard}
        COMMENT 'Power BI-ready daily equipment-health dataset'
        AS SELECT d.calendar_date, d.year, d.month, d.month_name, d.week_of_year,
                  e.equipment_name, e.equipment_type, f.* EXCEPT (equipment_id, date_key)
        FROM {daily} f
        JOIN {dates} d ON f.date_key = d.date_key
        JOIN {equipment} e ON f.equipment_id = e.equipment_id
    """)


def validate_pipeline(spark, config: PipelineConfig, run_id: str) -> list[dict]:
    from datetime import datetime, timezone

    bronze_count = spark.table(config.table("bronze", "sensor_readings_raw")).count()
    silver_count = spark.table(config.table("silver", "sensor_readings")).count()
    reject_count = spark.table(config.table("silver", "sensor_readings_rejects")).count()
    fact_count = spark.table(config.table("gold", "fact_sensor_reading")).count()
    duplicate_count = spark.sql(
        f"SELECT count(*) FROM (SELECT reading_id, event_ts FROM {config.table('silver', 'sensor_readings')} "
        "GROUP BY reading_id, event_ts HAVING count(*) > 1)"
    ).first()[0]
    checks = [
        {"check_name": "bronze_reconciles_to_silver_and_rejects", "passed": bronze_count == silver_count + reject_count,
         "actual": bronze_count, "expected": silver_count + reject_count},
        {"check_name": "silver_key_is_unique", "passed": duplicate_count == 0,
         "actual": duplicate_count, "expected": 0},
        {"check_name": "gold_fact_matches_silver", "passed": fact_count == silver_count,
         "actual": fact_count, "expected": silver_count},
        {"check_name": "gold_dimensions_are_populated", "passed": spark.table(config.table('gold', 'dim_date')).count() > 0,
         "actual": spark.table(config.table('gold', 'dim_date')).count(), "expected": 1},
    ]
    checked_at = datetime.now(timezone.utc)
    rows = [(run_id, item["check_name"], item["passed"], item["actual"], item["expected"], checked_at) for item in checks]
    spark.createDataFrame(
        rows, "run_id string, check_name string, passed boolean, actual long, expected long, checked_at timestamp"
    ).write.format("delta").mode("append").saveAsTable(config.table("audit", "pipeline_validation_results"))
    failed = [item for item in checks if not item["passed"]]
    if failed:
        raise RuntimeError(f"Pipeline acceptance checks failed: {failed}")
    return checks
