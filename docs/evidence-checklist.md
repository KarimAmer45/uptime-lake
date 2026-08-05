# Cloud evidence capture checklist

These artifacts must come from the real deployed workspace. Do not replace them with mockups.

- `docs/databricks_job_run.png`: open Workflows, select the production job, and capture all five tasks green
  with the run timestamp visible.
- `docs/unity_catalog_lineage.png`: open Catalog Explorer > `metro.gold.fact_sensor_reading` > Lineage and
  capture upstream Silver/Bronze nodes.
- `docs/unity_catalog_grants.png`: capture Gold schema permissions showing the read-only analyst group.
- `docs/powerbi_equipment_health.png`: refresh the report, set the full date range, and export a 16:9 image.
- `artifacts/production_metrics.json`: record Bronze, Silver, rejects, Gold, per-check pass rates, and job run
  URL from `sql/portfolio_queries.sql`.

Before publishing, remove workspace IDs, personal email addresses, storage-account secrets, and access tokens.

