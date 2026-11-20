# Week 3: Day-Wise Activity Guide

A comprehensive, consolidated roadmap of all day-wise tasks, setup procedures, and deployment workflows for the **Cybersecurity Analyzer** project across Day 1 and Day 2.

---

## Table of Contents
1. [Day 1 Overview](#day-1-local-development--azure-deployment)
   - [Day 1 Part 0: Getting Started & Local Testing](#day-1-part-0-getting-started--local-testing)
   - [Day 1 Part 1: Azure Account & Environment Setup](#day-1-part-1-azure-account--environment-setup)
   - [Day 1 Part 2: Azure Deployment with Terraform](#day-1-part-2-azure-deployment-with-terraform)
2. [Day 2 Overview](#day-2-google-cloud-platform-gcp-deployment)
   - [Day 2 Part 1: GCP Account & Project Setup](#day-2-part-1-gcp-account--project-setup)
   - [Day 2 Part 2: Cloud Run Deployment with Terraform](#day-2-part-2-cloud-run-deployment-with-terraform)
3. [Cloud Comparison: Azure Container Apps vs. Google Cloud Run](#cloud-comparison-azure-vs-gcp)
4. [Master Command Cheat Sheet](#master-command-cheat-sheet)

---

## Day 1: Local Development & Azure Deployment

### Day 1 Part 0: Getting Started & Local Testing
Detailed Guide: [day1.part0.md](./day1.part0.md)

* **Goal**: Prepare your local development environment, configure API keys, and test the Cybersecurity Analyzer locally with and without Docker.
* **Key Tasks**:
  1. **Project Setup**:
     - Clone repository: `git clone https://github.com/ed-donner/cyber.git`
     - Open the project directory in Cursor.
  2. **Semgrep Setup**:
     - Create an account at [semgrep.dev](https://semgrep.dev).
     - Generate a new API token with **Agent (CI)** and **Web API** permissions enabled.
  3. **Environment Configuration**:
     - Configure `.env` in the project root:
       ```env
       # Use either GEMINI_API_KEY or OPENAI_API_KEY:
       GEMINI_API_KEY=your-gemini-key-here
       OPENAI_API_KEY=your-openai-key-here
       SEMGREP_APP_TOKEN=your-semgrep-token-here
       ```
       *(Note: If using Gemini, the backend automatically connects via Google's OpenAI-compatible endpoint with `gemini-2.5-flash`)*
  4. **Run Locally (Two Separate Terminals)**:
     - **Backend** (FastAPI):
       ```bash
       cd backend
       uv run server.py
       ```
       *(Runs on `http://localhost:8000`)*
     - **Frontend** (Next.js):
       ```bash
       cd frontend
       npm install
       npm run dev
       ```
       *(Runs on `http://localhost:3000`)*
     - **Validation**: Open `http://localhost:3000`, upload `airline.py`, and run analysis to confirm vulnerabilities are identified.
  5. **Run as Single Docker Container**:
     - Build image:
       ```bash
       docker build -t cyber-analyzer .
       ```
     - Run container:
       ```bash
       docker run --rm --name cyber-analyzer -p 8000:8000 --env-file .env cyber-analyzer
       ```
     - Test at `http://localhost:8000` with `airline.py`.

---

### Day 1 Part 1: Azure Account & Environment Setup
Detailed Guide: [day1.part1.md](./day1.part1.md)

* **Goal**: Create and configure an Azure account, set up budgets and billing protections, and initialize the Azure CLI.
* **Key Tasks**:
  1. **Account Registration**:
     - Register for an Azure Free Account or Azure for Students ($200/$100 credit).
  2. **Hierarchy & Organization**:
     - Understand Subscription $\rightarrow$ Resource Group $\rightarrow$ Resources structure.
  3. **Budget Alert Setup**:
     - Navigate to **Cost Management + Billing** $\rightarrow$ **Budgets**.
     - Set a monthly budget of **$10** with email alert thresholds at 50%, 80%, and 100%.
  4. **Resource Group Creation**:
     - Create Resource Group: `cyber-analyzer-rg` in your closest region (e.g., `East US`).
  5. **Azure CLI Setup & Verification**:
     - Install Azure CLI (`az`).
     - Authenticate via browser:
       ```bash
       az login
       ```
     - Verify active subscriptions and resource groups:
       ```bash
       az account list --output table
       az group list --output table
       ```

---

### Day 1 Part 2: Azure Deployment with Terraform
Detailed Guide: [day1.part2.md](./day1.part2.md)

* **Goal**: Deploy the Cybersecurity Analyzer container to Azure Container Apps (ACA) and Azure Container Registry (ACR) using Terraform.
* **Key Tasks**:
  1. **Load Environment Variables**:
     - **PowerShell**:
       ```powershell
       Get-Content .env | ForEach-Object {
           $name, $value = $_.split('=', 2)
           Set-Item -Path "env:$name" -Value $value
       }
       ```
     - **Bash / zsh**:
       ```bash
       export $(cat .env | xargs)
       ```
  2. **Terraform Initialization & Workspace Setup**:
     ```bash
     cd terraform/azure
     terraform init
     terraform workspace new azure
     terraform workspace select azure
     ```
  3. **Register Azure Resource Providers**:
     ```bash
     az provider register --namespace Microsoft.App
     az provider register --namespace Microsoft.OperationalInsights
     ```
     *(Wait until `registrationState` shows `Registered`)*
  4. **Deploy Infrastructure**:
     - **PowerShell**:
       ```powershell
       terraform plan -var ("openai_api_key=" + $Env:OPENAI_API_KEY) -var ("semgrep_app_token=" + $Env:SEMGREP_APP_TOKEN)
       terraform apply -var ("openai_api_key=" + $Env:OPENAI_API_KEY) -var ("semgrep_app_token=" + $Env:SEMGREP_APP_TOKEN)
       ```
     - **Bash**:
       ```bash
       terraform plan -var="openai_api_key=$OPENAI_API_KEY" -var="semgrep_app_token=$SEMGREP_APP_TOKEN"
       terraform apply -var="openai_api_key=$OPENAI_API_KEY" -var="semgrep_app_token=$SEMGREP_APP_TOKEN"
       ```
  5. **Verification & Testing**:
     - Retrieve application URL:
       ```bash
       terraform output app_url
       ```
     - Open in browser, upload `airline.py`, and inspect logs:
       ```bash
       az containerapp logs show --name cyber-analyzer --resource-group cyber-analyzer-rg --follow
       ```
  6. **Resource Teardown (Crucial to prevent ongoing charges)**:
     - Run `terraform destroy` passing API key variables.

---

## Day 2: Google Cloud Platform (GCP) Deployment

### Day 2 Part 1: GCP Account & Project Setup
Detailed Guide: [day2.part1.md](./day2.part1.md)

* **Goal**: Set up Google Cloud Platform, initialize the gcloud CLI, configure billing and cost alerts, and enable required container APIs.
* **Key Tasks**:
  1. **Account Registration**:
     - Sign up for GCP Free Trial ($300 credit for 90 days; no auto-charge after trial ends).
  2. **Project Creation**:
     - Create project `cyber-analyzer` in Google Cloud Console.
     - Note the globally unique **Project ID** (e.g., `cyber-analyzer-123456`).
  3. **Billing & Budget Management**:
     - Link Billing Account to `cyber-analyzer`.
     - Set up a monthly training budget of **$10** with 50%, 90%, and 100% threshold alerts.
  4. **Google Cloud CLI Initialization**:
     - Install `gcloud` CLI.
     - Initialize and log in:
       ```bash
       gcloud init
       ```
     - Set default project and default compute region (e.g., `us-central1`).
  5. **Enable Cloud APIs**:
     ```bash
     gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com
     ```

---

### Day 2 Part 2: Cloud Run Deployment with Terraform
Detailed Guide: [day2.part2.md](./day2.part2.md)

* **Goal**: Deploy containerized application to Google Cloud Run and Google Container Registry using Terraform.
* **Key Tasks**:
  1. **Environment Variables**:
     - Set `TF_VAR_project_id="<your-gcp-project-id>"` alongside OpenAI and Semgrep keys.
  2. **Terraform Initialization & Workspace Setup**:
     ```bash
     cd terraform/gcp
     terraform init
     terraform workspace new gcp
     terraform workspace select gcp
     ```
  3. **Authenticate Docker and Terraform**:
     ```bash
     gcloud auth login
     gcloud auth application-default login
     gcloud auth application-default set-quota-project $TF_VAR_project_id
     gcloud auth configure-docker
     ```
  4. **Deploy Infrastructure**:
     - **PowerShell**:
       ```powershell
       terraform plan -var ("openai_api_key=" + $Env:OPENAI_API_KEY) -var ("semgrep_app_token=" + $Env:SEMGREP_APP_TOKEN)
       terraform apply -var ("openai_api_key=" + $Env:OPENAI_API_KEY) -var ("semgrep_app_token=" + $Env:SEMGREP_APP_TOKEN)
       ```
     - **Bash**:
       ```bash
       terraform plan -var="openai_api_key=$OPENAI_API_KEY" -var="semgrep_app_token=$SEMGREP_APP_TOKEN"
       terraform apply -var="openai_api_key=$OPENAI_API_KEY" -var="semgrep_app_token=$SEMGREP_APP_TOKEN"
       ```
  5. **Verification & Testing**:
     - Fetch service URL:
       ```bash
       terraform output service_url
       ```
     - Open in browser, test with `airline.py`, and inspect logs:
       ```bash
       gcloud run services logs read cyber-analyzer --limit=50
       ```
  6. **Google Workspace Restriction Handling (If Needed)**:
     - If encountering domain-restricted sharing errors (`allUsers` policy error): modify organizational policy or use local proxy:
       ```bash
       gcloud run services proxy cyber-analyzer --region=us-central1
       ```
  7. **Clean Up & Teardown**:
     - Run `terraform destroy` with API keys.
     - Remove leftover container images from registry:
       ```bash
       gcloud container images delete gcr.io/$TF_VAR_project_id/cyber-analyzer --quiet --force-delete-tags
       ```

---

## Cloud Comparison: Azure vs. GCP

| Feature | Azure Container Apps (ACA) | Google Cloud Run |
|---|---|---|
| **Cold Start** | ~30 seconds | ~5–10 seconds |
| **True Scale-to-Zero** | Partial (background system processes) | Complete ($0 idle compute cost) |
| **Billing Model** | Per vCPU/Memory allocated | Per request + compute duration |
| **Image Registry** | Azure Container Registry (ACR) | Artifact Registry / Google Container Registry (GCR) |
| **Free Tier** | Limited free credits | 2M requests/month free forever |
| **Resource Needs** | 1.0 vCPU, 2.0 GiB RAM (required for Semgrep) | 1.0 vCPU, 2.0 GiB RAM (required for Semgrep) |

---

## Master Command Cheat Sheet

### Local Testing
```bash
# Backend
cd backend && uv run server.py

# Frontend
cd frontend && npm install && npm run dev

# Docker
docker build -t cyber-analyzer .
docker run --rm --name cyber-analyzer -p 8000:8000 --env-file .env cyber-analyzer
```

### Azure Deployment & Teardown
```bash
cd terraform/azure
terraform init
terraform workspace select azure

# Apply
terraform apply -var="openai_api_key=$OPENAI_API_KEY" -var="semgrep_app_token=$SEMGREP_APP_TOKEN"

# Destroy
terraform destroy -var="openai_api_key=$OPENAI_API_KEY" -var="semgrep_app_token=$SEMGREP_APP_TOKEN"
```

### GCP Deployment & Teardown
```bash
cd terraform/gcp
terraform init
terraform workspace select gcp

# Apply
terraform apply -var="openai_api_key=$OPENAI_API_KEY" -var="semgrep_app_token=$SEMGREP_APP_TOKEN"

# Destroy
terraform destroy -var="openai_api_key=$OPENAI_API_KEY" -var="semgrep_app_token=$SEMGREP_APP_TOKEN"
```
