-- Run as a Unity Catalog metastore admin after replacing the placeholders.
-- The bundle performs equivalent grants when --var read_principal=<group> is supplied.

GRANT USE CATALOG ON CATALOG metro TO `data_analysts`;
GRANT USE SCHEMA ON SCHEMA metro.gold TO `data_analysts`;
GRANT SELECT ON SCHEMA metro.gold TO `data_analysts`;

-- Quality reviewers can inspect rejects but cannot modify them.
GRANT USE CATALOG ON CATALOG metro TO `data_quality_reviewers`;
GRANT USE SCHEMA ON SCHEMA metro.silver TO `data_quality_reviewers`;
GRANT SELECT ON TABLE metro.silver.sensor_readings_rejects TO `data_quality_reviewers`;

SHOW GRANTS ON SCHEMA metro.gold;
SHOW GRANTS ON TABLE metro.silver.sensor_readings_rejects;

