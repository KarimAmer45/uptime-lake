# Azure deployment runbook

This is the single supported production path. It creates billable Azure resources; use a budget alert and
delete the resource group after capturing portfolio evidence.

## 1. Prerequisites

- Azure subscription with permission to create resource groups, role assignments, ADLS Gen2, and Azure
  Databricks.
- Azure CLI, Databricks CLI 0.218 or newer, Python 3.10+, and a Unity Catalog metastore attached to the
  workspace.
- Power BI Desktop on Windows for the final report artifact.

## 2. Provision the minimal Azure resources

```powershell
az login
az account set --subscription "<subscription-id>"
az group create --name rg-uptime-lake --location westeurope
az deployment group create `
  --resource-group rg-uptime-lake `
  --template-file infra/main.bicep `
  --parameters prefix=<globally-unique-prefix>
az deployment group show --resource-group rg-uptime-lake --name main --query properties.outputs
```

Set an Azure budget alert before starting compute. The job uses a small, single-node cluster and the bundle
schedule is paused in `dev`.

## 3. Register ADLS with Unity Catalog

Use the deployment outputs to replace placeholders in `infra/external_location.sql`, then run it as a Unity
Catalog metastore admin. This creates a managed-identity storage credential and external location; no account
keys or secrets enter the repository.

## 4. Download and land the source

MetroPT-3 is CC BY 4.0. The script downloads the official UCI archive, extracts only the expected CSV, and
fails unless it finds exactly 1,516,948 data rows.

```powershell
python scripts/download_metropt3.py
./scripts/upload_to_adls.ps1 `
  -StorageAccount <storage-account-output> `
  -FileSystem raw
```

## 5. Validate and deploy the Databricks Asset Bundle

```powershell
databricks auth login --host https://<workspace-url> --profile uptime-lake
databricks bundle validate --target dev --profile uptime-lake `
  --var="source_path=abfss://raw@<storage>.dfs.core.windows.net/metropt3/MetroPT3(AirCompressor).csv" `
  --var="read_principal=data_analysts"
databricks bundle deploy --target dev --profile uptime-lake `
  --var="source_path=abfss://raw@<storage>.dfs.core.windows.net/metropt3/MetroPT3(AirCompressor).csv" `
  --var="read_principal=data_analysts"
databricks bundle run metropt_lakehouse --target dev --profile uptime-lake
```

After the dev run passes, deploy `--target prod`. Production unpauses the weekly Sunday 06:00 Europe/Berlin
schedule. If that cadence is not desired, leave `schedule_pause_status=PAUSED` and use a different approved
schedule before deployment.

## 6. Capture evidence and control cost

Run `sql/portfolio_queries.sql`, save quantified metrics, and follow `docs/evidence-checklist.md`. Only after
all real screenshots and metrics are committed should the README checklist and CV bullets be marked complete.

To stop spend, pause the production job and terminate its cluster. When the demo is no longer needed, delete
the exact resource group created above:

```powershell
az group delete --name rg-uptime-lake
```

Resource-group deletion is irreversible; confirm that the group contains only this project first.

