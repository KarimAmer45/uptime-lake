# Databricks notebook source
"""Land MetroPT-3 CSV from ADLS/Volumes into the auditable Bronze Delta table."""

# COMMAND ----------

from datetime import datetime, timezone

from uptime_lake.config import PipelineConfig
from uptime_lake.pipeline import ingest_bronze

dbutils.widgets.text("catalog", "metro_dev")
dbutils.widgets.text("source_path", "")
dbutils.widgets.text("run_id", "standalone")

catalog = dbutils.widgets.get("catalog")
source_path = dbutils.widgets.get("source_path")
run_id = dbutils.widgets.get("run_id") or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

row_count = ingest_bronze(spark, PipelineConfig(catalog=catalog), source_path, run_id)
assert row_count > 0, "Bronze ingestion produced no rows"
print({"bronze_rows": row_count, "source_path": source_path, "run_id": run_id})

