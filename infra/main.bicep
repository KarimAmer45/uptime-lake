targetScope = 'resourceGroup'

@description('Globally unique lowercase prefix, 3-12 characters.')
@minLength(3)
@maxLength(12)
param prefix string

param location string = resourceGroup().location
param databricksSku string = 'premium'

var storageName = take(toLower(replace('${prefix}iotlake', '-', '')), 24)
var workspaceName = '${prefix}-databricks'
var connectorName = '${prefix}-access-connector'
var blobContributorRole = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
)

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    isHnsEnabled: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource rawContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'raw'
  properties: { publicAccess: 'None' }
}

resource connector 'Microsoft.Databricks/accessConnectors@2023-05-01' = {
  name: connectorName
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {}
}

resource storageRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, connector.id, blobContributorRole)
  scope: storage
  properties: {
    principalId: connector.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: blobContributorRole
  }
}

resource workspace 'Microsoft.Databricks/workspaces@2024-05-01' = {
  name: workspaceName
  location: location
  sku: { name: databricksSku }
  properties: {
    managedResourceGroupId: subscriptionResourceId(
      'Microsoft.Resources/resourceGroups',
      '${resourceGroup().name}-${workspaceName}-managed'
    )
    publicNetworkAccess: 'Enabled'
    requiredNsgRules: 'AllRules'
  }
}

output storageAccountName string = storage.name
output rawAbfssUrl string = 'abfss://${rawContainer.name}@${storage.name}.dfs.core.windows.net/'
output accessConnectorId string = connector.id
output databricksWorkspaceName string = workspace.name
output databricksWorkspaceUrl string = workspace.properties.workspaceUrl

