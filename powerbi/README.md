# Power BI report handoff

The repository contains the source query, measures, theme, and a pixel-specific report specification. A
binary `.pbix` is intentionally not fabricated: it must be created/refreshed by Power BI Desktop against
the deployed Unity Catalog view so its screenshot is genuine.

1. Deploy and run the Databricks job successfully.
2. In Power BI Desktop, select **Get data > Azure Databricks**. Enter the SQL warehouse server hostname and
   HTTP path, then choose catalog `metro`, schema `gold`, view `powerbi_equipment_health`.
3. Use Import mode for this portfolio-sized daily table. `PowerQuery.m` is the equivalent parameterized M
   query; create text parameters `DatabricksServerHostname`, `DatabricksHttpPath`, and `DatabricksCatalog`.
4. Add the measures from `measures.dax`, import `theme.json`, and build the visuals in
   `dashboard_spec.md`.
5. Save as `powerbi/MetroPT Equipment Health.pbix` locally (the binary is gitignored unless you choose to
   publish it with Git LFS). Export a screenshot to `docs/powerbi_equipment_health.png`.

The Azure Databricks connector supports Import and DirectQuery. This project uses Import because the Gold
view is already daily-grain and small; it keeps the public demo responsive and inexpensive.

