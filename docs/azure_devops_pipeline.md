# Azure DevOps CI/CD Pipeline for MCP SDK and Scheduler

This document outlines how to set up a CI/CD pipeline using Azure DevOps for the MCP SDK integration and Scheduler service.

## Prerequisites

- Azure DevOps organization and project
- Azure subscription
- MCP SDK integrated project as described in [MCP SDK Integration Guide](mcp_sdk_integration.md)
- Azure resources as outlined in [Azure Integration Guide](azure_integration_guide.md)

## Pipeline Overview

The CI/CD pipeline will consist of the following stages:

1. **Build**: Compile and package the application
2. **Test**: Run unit and integration tests
3. **Deploy to Dev**: Deploy to development environment
4. **Test Integration**: Run end-to-end integration tests
5. **Deploy to Production**: Deploy to production environment

## Setup Instructions

### 1. Repository Setup

1. Initialize your repo with Azure DevOps:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://dev.azure.com/your-org/your-project/_git/your-repo
git push -u origin main
```

### 2. Create Azure DevOps Pipeline

1. Create a file named `azure-pipelines.yml` in your repository root:

```yaml
# CI/CD pipeline for MCP SDK and Scheduler
trigger:
  branches:
    include:
      - main
      - develop
  paths:
    exclude:
      - "*.md"
      - "docs/*"

variables:
  # Pipeline variables
  pythonVersion: "3.10"
  vmImageName: "ubuntu-latest"
  appName: "mcp-scheduler-app"
  appServicePlanName: "mcp-scheduler-plan"
  resourceGroupName: "mcp-scheduler-rg"
  azureSubscription: "your-azure-subscription"
  keyVaultName: "mcp-scheduler-kv"

stages:
  - stage: Build
    displayName: "Build"
    jobs:
      - job: BuildJob
        displayName: "Build and Package Application"
        pool:
          vmImage: $(vmImageName)
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: "$(pythonVersion)"
              addToPath: true
            displayName: "Set up Python"

          - script: |
              python -m pip install --upgrade pip
              pip install -r requirements.txt
            displayName: "Install dependencies"

          - script: |
              pip install pytest pytest-cov pylint mypy
              pylint app/ scripts/ --disable=C0111
              mypy app/ scripts/
            displayName: "Lint and static analysis"

          - script: |
              pytest tests/ --cov=app --cov-report=xml
            displayName: "Run unit tests"

          - task: PublishCodeCoverageResults@1
            inputs:
              codeCoverageTool: Cobertura
              summaryFileLocation: "$(System.DefaultWorkingDirectory)/coverage.xml"
            displayName: "Publish code coverage results"

          - task: ArchiveFiles@2
            inputs:
              rootFolderOrFile: "$(System.DefaultWorkingDirectory)"
              includeRootFolder: false
              archiveType: "zip"
              archiveFile: "$(Build.ArtifactStagingDirectory)/app.zip"
              replaceExistingArchive: true
            displayName: "Archive Files"

          - task: PublishBuildArtifacts@1
            inputs:
              pathToPublish: "$(Build.ArtifactStagingDirectory)/app.zip"
              artifactName: "drop"
            displayName: "Publish Build Artifacts"

  - stage: DeployToDev
    displayName: "Deploy to Dev Environment"
    dependsOn: Build
    jobs:
      - job: DeployDevJob
        displayName: "Deploy Application to Dev"
        pool:
          vmImage: $(vmImageName)
        steps:
          - task: DownloadBuildArtifacts@0
            inputs:
              buildType: "current"
              downloadType: "single"
              artifactName: "drop"
              downloadPath: "$(System.ArtifactsDirectory)"
            displayName: "Download Build Artifacts"

          - task: AzureWebApp@1
            inputs:
              azureSubscription: "$(azureSubscription)"
              appType: "webApp"
              appName: "$(appName)-dev"
              resourceGroupName: "$(resourceGroupName)"
              package: "$(System.ArtifactsDirectory)/drop/app.zip"
              deploymentMethod: "auto"
            displayName: "Deploy to Azure Web App - Dev"

          - task: AzureAppServiceSettings@1
            inputs:
              azureSubscription: "$(azureSubscription)"
              appName: "$(appName)-dev"
              resourceGroupName: "$(resourceGroupName)"
              appSettings: |
                [
                  {
                    "name": "USE_AZURE_SERVICES",
                    "value": "true"
                  },
                  {
                    "name": "KEYVAULT_URI",
                    "value": "https://$(keyVaultName).vault.azure.net/"
                  },
                  {
                    "name": "APPINSIGHTS_INSTRUMENTATIONKEY",
                    "value": "$(appInsightsKey)"
                  },
                  {
                    "name": "WEBSITE_RUN_FROM_PACKAGE",
                    "value": "1"
                  }
                ]
            displayName: "Configure App Service Settings"

  - stage: TestIntegration
    displayName: "Test Integration"
    dependsOn: DeployToDev
    jobs:
      - job: IntegrationTestJob
        displayName: "Run Integration Tests"
        pool:
          vmImage: $(vmImageName)
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: "$(pythonVersion)"
              addToPath: true
            displayName: "Set up Python"

          - script: |
              python -m pip install --upgrade pip
              pip install -r requirements.txt
              pip install pytest requests
            displayName: "Install dependencies"

          - script: |
              # Set environment variables for testing
              export TEST_APP_URL=https://$(appName)-dev.azurewebsites.net
              export TEST_CLIENT_ID=$(clientId)
              export TEST_API_KEY=$(apiKey)

              # Run integration tests against deployed app
              pytest tests/integration/ -v
            displayName: "Run integration tests"
            env:
              clientId: $(CLIENT_ID)
              apiKey: $(API_KEY)

  - stage: DeployToProd
    displayName: "Deploy to Production"
    dependsOn: TestIntegration
    condition: succeeded()
    jobs:
      - deployment: DeployProd
        displayName: "Deploy Application to Production"
        environment: "production"
        pool:
          vmImage: $(vmImageName)
        strategy:
          runOnce:
            deploy:
              steps:
                - task: DownloadBuildArtifacts@0
                  inputs:
                    buildType: "current"
                    downloadType: "single"
                    artifactName: "drop"
                    downloadPath: "$(System.ArtifactsDirectory)"
                  displayName: "Download Build Artifacts"

                - task: AzureRmWebAppDeployment@4
                  inputs:
                    ConnectionType: "AzureRM"
                    azureSubscription: "$(azureSubscription)"
                    appType: "webApp"
                    WebAppName: "$(appName)"
                    ResourceGroupName: "$(resourceGroupName)"
                    packageForLinux: "$(System.ArtifactsDirectory)/drop/app.zip"
                    enableCustomDeployment: true
                    DeploymentType: "webDeploy"
                    TakeAppOfflineFlag: true
                  displayName: "Deploy to Azure Web App - Prod"

                - task: AzureAppServiceSettings@1
                  inputs:
                    azureSubscription: "$(azureSubscription)"
                    appName: "$(appName)"
                    resourceGroupName: "$(resourceGroupName)"
                    appSettings: |
                      [
                        {
                          "name": "USE_AZURE_SERVICES",
                          "value": "true"
                        },
                        {
                          "name": "KEYVAULT_URI",
                          "value": "https://$(keyVaultName).vault.azure.net/"
                        },
                        {
                          "name": "APPINSIGHTS_INSTRUMENTATIONKEY",
                          "value": "$(appInsightsKeyProd)"
                        },
                        {
                          "name": "WEBSITE_RUN_FROM_PACKAGE",
                          "value": "1"
                        }
                      ]
                  displayName: "Configure App Service Settings"
```

### 3. Set Up Pipeline Variables

1. In Azure DevOps, go to Pipelines > Library > Variable Groups
2. Create a new Variable Group named "MCP-Scheduler-Variables"
3. Add the following variables:
   - `appInsightsKey`: Instrumentation key for dev environment
   - `appInsightsKeyProd`: Instrumentation key for prod environment
   - `CLIENT_ID`: Scheduler client ID (marked as secret)
   - `API_KEY`: Scheduler API key (marked as secret)

### 4. Configure Azure DevOps Service Connections

1. In Azure DevOps, go to Project Settings > Service Connections
2. Create a new Azure Resource Manager connection named "your-azure-subscription"
3. Select your subscription and create the connection
4. Grant permissions to the pipeline to use this connection

### 5. Create Integration Tests

Create integration tests in the `tests/integration` directory:

```python
# tests/integration/test_scheduler_integration.py
import os
import pytest
import requests
import json
import time
from datetime import datetime, timedelta

# Test variables
TEST_APP_URL = os.environ.get("TEST_APP_URL", "http://localhost:8000")
TEST_CLIENT_ID = os.environ.get("TEST_CLIENT_ID")
TEST_API_KEY = os.environ.get("TEST_API_KEY")

def test_scheduler_health():
    """Test that the scheduler service is healthy."""
    response = requests.get(f"{TEST_APP_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_scheduler_auth():
    """Test authentication against the scheduler service."""
    # Request JWT token
    auth_payload = {
        "clientId": TEST_CLIENT_ID,
        "apiKey": TEST_API_KEY
    }

    response = requests.post(
        f"{TEST_APP_URL}/api/auth/token",
        json=auth_payload
    )

    assert response.status_code == 200
    assert "token" in response.json()

def test_schedule_conversation():
    """Test scheduling a conversation."""
    # First authenticate
    auth_payload = {
        "clientId": TEST_CLIENT_ID,
        "apiKey": TEST_API_KEY
    }

    auth_response = requests.post(
        f"{TEST_APP_URL}/api/auth/token",
        json=auth_payload
    )

    token = auth_response.json()["token"]

    # Schedule a conversation
    scheduled_time = (datetime.now() + timedelta(minutes=5)).isoformat()

    schedule_payload = {
        "conversationText": "This is a test scheduled message",
        "scheduledTime": scheduled_time,
        "endpoint": "https://example.com/callback"
    }

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(
        f"{TEST_APP_URL}/api/scheduler/schedule",
        json=schedule_payload,
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "conversationId" in data

    conversation_id = data["conversationId"]

    # Check conversation status
    status_response = requests.get(
        f"{TEST_APP_URL}/api/scheduler/status/{conversation_id}",
        headers=headers
    )

    assert status_response.status_code == 200
    assert status_response.json()["status"] in ["Scheduled", "InProgress"]

    # Cancel conversation
    cancel_response = requests.delete(
        f"{TEST_APP_URL}/api/scheduler/{conversation_id}",
        headers=headers
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["cancelled"] == True
```

### 6. Azure App Service and Key Vault Setup

1. Set up Azure Key Vault and App Service as described in [Azure Integration Guide](azure_integration_guide.md)

2. Ensure the App Service has managed identity enabled and has access to Key Vault

3. Create a deployment slot for development:

```bash
az webapp deployment slot create \
  --name $appName \
  --resource-group $resourceGroupName \
  --slot dev
```

### 7. Configure Branch Policies

1. Go to Repos > Branches
2. Select your main branch and add a branch policy
3. Require a minimum number of reviewers
4. Require the build to pass before merging
5. Apply branch policies to protect your main branch

## Workflow

1. Developers work on feature branches
2. Pull requests are created to merge into the develop branch
3. The pipeline builds and tests the changes
4. After approval, changes are merged to develop
5. The pipeline deploys to the development environment
6. Integration tests run against the dev environment
7. After approval, changes are merged to main
8. The pipeline deploys to the production environment

## Monitoring and Alerting

Set up monitoring and alerting to ensure the health of your deployment:

1. In the Azure portal, go to your App Service
2. Select "Monitoring" > "Alerts"
3. Create alerts for:
   - HTTP 5xx errors
   - Server response time above threshold
   - Failed authentication attempts

## Rollback Procedure

If a deployment fails or introduces issues:

1. Use the Azure DevOps pipeline to redeploy the previous successful version
2. Or use Azure App Service deployment slots to swap back to the previous version:

```bash
az webapp deployment slot swap \
  --resource-group $resourceGroupName \
  --name $appName \
  --slot staging \
  --target-slot production
```

## Conclusion

This CI/CD pipeline provides a robust solution for deploying the MCP SDK and Scheduler service to Azure environments. The pipeline ensures that code is properly tested before deployment and that the application is deployed consistently across environments.

For more information on CI/CD practices, refer to:

- [Azure DevOps Documentation](https://docs.microsoft.com/en-us/azure/devops/)
- [CI/CD Best Practices](https://docs.microsoft.com/en-us/azure/devops/pipelines/ecosystems/python-webapp)
- [Azure Web App Deployment](https://docs.microsoft.com/en-us/azure/app-service/deploy-continuous-deployment)
