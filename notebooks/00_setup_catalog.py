# Databricks notebook source
"""Create the governed Unity Catalog namespace before each idempotent run."""

# COMMAND ----------

from datetime import datetime, timezone

from uptime_lake.config import PipelineConfig
from uptime_lake.pipeline import setup_catalog

dbutils.widgets.text("catalog", "metro_dev")
dbutils.widgets.text("read_principal", "")
dbutils.widgets.text("run_id", "standalone")

catalog = dbutils.widgets.get("catalog")
read_principal = dbutils.widgets.get("read_principal")
run_id = dbutils.widgets.get("run_id") or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

setup_catalog(spark, PipelineConfig(catalog=catalog), read_principal=read_principal)
print({"catalog": catalog, "run_id": run_id, "gold_read_principal": read_principal or None})

