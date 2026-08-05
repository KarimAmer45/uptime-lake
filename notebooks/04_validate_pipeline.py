# Databricks notebook source
"""Fail the scheduled job unless all layer reconciliation checks pass."""

# COMMAND ----------

from datetime import datetime, timezone

from uptime_lake.config import PipelineConfig
from uptime_lake.pipeline import validate_pipeline

dbutils.widgets.text("catalog", "metro_dev")
dbutils.widgets.text("run_id", "standalone")

catalog = dbutils.widgets.get("catalog")
run_id = dbutils.widgets.get("run_id") or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
checks = validate_pipeline(spark, PipelineConfig(catalog=catalog), run_id)

print({"status": "PASS", "checks": checks, "run_id": run_id})

