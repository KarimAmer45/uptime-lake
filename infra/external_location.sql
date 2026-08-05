-- Replace values from `az deployment group show --query properties.outputs`.
-- Run as a Unity Catalog metastore admin.

CREATE STORAGE CREDENTIAL IF NOT EXISTS metro_adls_credential
WITH AZURE_MANAGED_IDENTITY (
  ACCESS_CONNECTOR_ID = '/subscriptions/<subscription>/resourceGroups/<resource-group>/providers/Microsoft.Databricks/accessConnectors/<connector>'
)
COMMENT 'Managed identity used by the MetroPT-3 landing zone';

CREATE EXTERNAL LOCATION IF NOT EXISTS metro_raw
URL 'abfss://raw@<storage-account>.dfs.core.windows.net/'
WITH (STORAGE CREDENTIAL metro_adls_credential)
COMMENT 'ADLS Gen2 raw landing zone for MetroPT-3';

GRANT READ FILES ON EXTERNAL LOCATION metro_raw TO `<pipeline-runner>`;

LIST 'abfss://raw@<storage-account>.dfs.core.windows.net/metropt3/';

