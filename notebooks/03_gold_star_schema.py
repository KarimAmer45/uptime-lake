# Databricks notebook source
"""Build the Gold star schema and explainable equipment-health KPIs with Spark SQL."""

# COMMAND ----------

from uptime_lake.config import PipelineConfig
from uptime_lake.pipeline import build_gold

dbutils.widgets.text("catalog", "metro_dev")
dbutils.widgets.text("run_id", "standalone")

catalog = dbutils.widgets.get("catalog")
build_gold(spark, PipelineConfig(catalog=catalog))

display(spark.table(f"`{catalog}`.`gold`.`powerbi_equipment_health`").orderBy("calendar_date"))

