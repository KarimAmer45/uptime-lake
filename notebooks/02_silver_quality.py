# Databricks notebook source
"""Apply the typed data contract and route every failing row to a rejects table."""

# COMMAND ----------

from datetime import datetime, timezone

from uptime_lake.config import PipelineConfig
from uptime_lake.pipeline import build_silver

dbutils.widgets.text("catalog", "metro_dev")
dbutils.widgets.text("run_id", "standalone")

catalog = dbutils.widgets.get("catalog")
run_id = dbutils.widgets.get("run_id") or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
valid_count, reject_count = build_silver(spark, PipelineConfig(catalog=catalog), run_id)

print({"silver_rows": valid_count, "reject_rows": reject_count, "run_id": run_id})

