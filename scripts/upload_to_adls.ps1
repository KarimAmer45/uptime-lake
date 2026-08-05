param(
    [Parameter(Mandatory = $true)][string]$StorageAccount,
    [Parameter(Mandatory = $true)][string]$FileSystem,
    [string]$Source = "data/raw/MetroPT3(AirCompressor).csv",
    [string]$Destination = "metropt3/MetroPT3(AirCompressor).csv"
)

$ErrorActionPreference = "Stop"
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI is required: https://learn.microsoft.com/cli/azure/install-azure-cli"
}
if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
    throw "Source file not found: $Source"
}

az storage fs file upload `
    --account-name $StorageAccount `
    --file-system $FileSystem `
    --source $Source `
    --path $Destination `
    --auth-mode login `
    --overwrite true

$resolvedSource = (Resolve-Path -LiteralPath $Source).Path
Write-Output "Uploaded $resolvedSource to abfss://$FileSystem@$StorageAccount.dfs.core.windows.net/$Destination"

