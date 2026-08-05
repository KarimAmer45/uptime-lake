"""Bronze-to-Silver typing, deduplication, and reject routing."""

from __future__ import annotations

from uptime_lake.contracts import BINARY_COLUMNS, PRESSURE_COLUMNS, QUALITY_CHECKS, SENSOR_COLUMNS

SILVER_NAMES = {
    "TP2": "tp2",
    "TP3": "tp3",
    "H1": "h1",
    "DV_pressure": "dv_pressure",
    "Reservoirs": "reservoirs",
    "Oil_temperature": "oil_temperature",
    "Motor_current": "motor_current",
    "COMP": "comp",
    "DV_eletric": "dv_electric",
    "Towers": "towers",
    "MPG": "mpg",
    "LPS": "lps",
    "Pressure_switch": "pressure_switch",
    "Oil_level": "oil_level",
    "Caudal_impulses": "caudal_impulses",
}


def apply_quality_gate(bronze_df, equipment_id: str):
    """Return a typed frame with semicolon-delimited rejection reasons."""
    from pyspark.sql import Window, functions as F

    typed = bronze_df.select(
        F.col("index").alias("raw_reading_id"),
        F.col("timestamp").alias("raw_timestamp"),
        F.col("index").cast("long").alias("reading_id"),
        F.to_timestamp("timestamp").alias("event_ts"),
        *[F.col(source).cast("double").alias(target) for source, target in SILVER_NAMES.items()],
        "_source_file",
        "_ingested_at",
        "_run_id",
        F.lit(equipment_id).alias("equipment_id"),
    )

    window = Window.partitionBy("reading_id", "event_ts").orderBy(
        F.col("_source_file"), F.col("_ingested_at")
    )
    typed = typed.withColumn("_duplicate_rank", F.row_number().over(window))

    pressure_columns = [SILVER_NAMES[column] for column in PRESSURE_COLUMNS]
    sensor_columns = [SILVER_NAMES[column] for column in SENSOR_COLUMNS]
    binary_columns = [SILVER_NAMES[column] for column in BINARY_COLUMNS]

    missing_sensor = F.lit(False)
    pressure_invalid = F.lit(False)
    binary_invalid = F.lit(False)
    for column in sensor_columns:
        missing_sensor = missing_sensor | F.col(column).isNull()
    for column in pressure_columns:
        pressure_invalid = pressure_invalid | ~F.col(column).between(-2.0, 20.0)
    for column in binary_columns:
        binary_invalid = binary_invalid | ~F.col(column).isin(0.0, 1.0)

    reasons = F.concat_ws(
        "; ",
        F.when(F.col("reading_id").isNull(), "invalid_reading_id"),
        F.when(F.col("event_ts").isNull(), "invalid_timestamp"),
        F.when(
            F.col("event_ts").isNotNull()
            & ((F.col("event_ts") < F.lit("2020-01-01").cast("timestamp"))
               | (F.col("event_ts") >= F.lit("2021-01-01").cast("timestamp"))),
            "timestamp_outside_expected_window",
        ),
        F.when(missing_sensor, "missing_required_sensor"),
        F.when(pressure_invalid, "pressure_out_of_range"),
        F.when(~F.col("oil_temperature").between(-30.0, 150.0), "oil_temperature_out_of_range"),
        F.when(~F.col("motor_current").between(-1.0, 50.0), "motor_current_out_of_range"),
        F.when(binary_invalid, "invalid_binary_signal"),
        F.when(F.col("caudal_impulses") < 0, "negative_caudal_impulses"),
        F.when(F.col("_duplicate_rank") > 1, "duplicate_reading"),
    )
    return typed.withColumn("rejection_reason", reasons)


def split_quality_rows(quality_df):
    """Split valid rows from rejects while retaining raw identifiers on rejects."""
    from pyspark.sql import functions as F

    valid = (
        quality_df.filter(F.col("rejection_reason") == "")
        .drop("raw_reading_id", "raw_timestamp", "_duplicate_rank", "rejection_reason")
    )
    rejects = quality_df.filter(F.col("rejection_reason") != "").drop("_duplicate_rank")
    return valid, rejects


def quality_summary(spark, quality_df, run_id: str):
    """Aggregate every named row-level rule in one Spark action."""
    from datetime import datetime, timezone
    from pyspark.sql import functions as F

    reason_tokens = F.split(F.col("rejection_reason"), "; ")
    aggregates = [
        F.sum(F.when(F.array_contains(reason_tokens, check), 1).otherwise(0)).alias(check)
        for check in QUALITY_CHECKS
    ]
    counts = quality_df.agg(F.count("*").alias("checked_rows"), *aggregates).first().asDict()
    now = datetime.now(timezone.utc)
    rows = [
        (run_id, check, counts["checked_rows"], int(counts[check] or 0), now)
        for check in QUALITY_CHECKS
    ]
    return spark.createDataFrame(
        rows,
        "run_id string, check_name string, checked_rows long, failed_rows long, checked_at timestamp",
    ).withColumn("passed_rows", F.col("checked_rows") - F.col("failed_rows"))

