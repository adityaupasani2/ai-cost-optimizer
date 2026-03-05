# 🤖 AI Cost Optimizer

[![CI](https://github.com/adityaupasani2/ai-cost-optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/adityaupasani2/ai-cost-optimizer/actions)
[![Terraform](https://img.shields.io/badge/terraform-1.6-blueviolet)](https://www.terraform.io/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-1.29-blue)](https://kubernetes.io/)
[![Python](https://img.shields.io/badge/python-3.11-green)](https://python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> ML-powered DevOps platform that monitors, analyzes, and auto-optimizes AI/cloud infrastructure costs — live on AWS EKS.

---

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────┐
│                  GitHub Actions CI/CD                │
│         Terraform Lint → Test → Build → Deploy      │
└─────────────────────┬───────────────────────────────┘
                      │
         ┌────────────▼────────────┐
         │     Terraform (IaC)     │
         │   VPC · EKS · S3 · IAM  │
         └────────────┬────────────┘
                      │
    ┌─────────────────▼──────────────────┐
    │          AWS EKS Cluster            │
    │                                     │
    │  ┌─────────────┐  ┌─────────────┐  │
    │  │ Prometheus  │  │ AI Optimizer│  │
    │  │ + Grafana   │  │  FastAPI    │  │
    │  │ + Loki      │  │  ML Engine  │  │
    │  └──────┬──────┘  └──────┬──────┘  │
    │         │                │          │
    │  ┌──────▼────────────────▼───────┐  │
    │  │      LLM Cost Exporter        │  │
    │  │  OpenAI · Anthropic · Bedrock │  │
    │  └───────────────────────────────┘  │
    └─────────────────────────────────────┘
```

---

## 🚀 What This Does

This platform automatically:
- **Monitors** LLM API costs (OpenAI, Anthropic) via custom Prometheus exporter
- **Visualizes** real-time spend on Grafana dashboards
- **Detects** cost anomalies and idle resources via ML
- **Recommends** right-sizing, spot instances, and model switching
- **Deploys** infrastructure as code with cost estimates on every PR

---

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| **Infrastructure** | Terraform, AWS EKS, VPC, S3, IAM |
| **Orchestration** | Kubernetes, Helm, Karpenter |
| **Observability** | Prometheus, Grafana, Alertmanager, Loki |
| **AI Engine** | Python, FastAPI, scikit-learn, Prophet |
| **CI/CD** | GitHub Actions, Trivy, Infracost |
| **Cost Tracking** | Custom Prometheus Exporter, AWS Cost Explorer |

---

## 📊 Live Dashboards

| Dashboard | Description |
|---|---|
| Node Exporter Full | CPU, Memory, Disk per AWS node |
| Kubernetes POD Overview | Pod status, restarts, resource usage |
| LLM Cost Optimizer | Token usage, cost per model, anomalies |
| K8s Compute Resources | Cluster-wide resource efficiency |

---

## ⚡ Quick Start

### Prerequisites
- Terraform >= 1.5
- AWS CLI configured
- kubectl + helm
- Docker

### 1. Bootstrap Backend
```bash
chmod +x scripts/bootstrap-backend.sh
./scripts/bootstrap-backend.sh us-east-1 ai-cost-optimizer-tfstate
```

### 2. Deploy Infrastructure
```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

### 3. Connect to Cluster
```bash
aws eks update-kubeconfig --region us-east-1 --name ai-cost-optimizer-dev
kubectl get nodes
```

### 4. Deploy Monitoring Stack
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f k8s/helm-values/prometheus-stack.yaml
```

### 5. Deploy AI Optimizer API
```bash
kubectl apply -f k8s/base/optimizer-deployment.yaml
kubectl get svc -n cost-optimizer
```

---

## 🤖 API Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Health check |
| `GET /recommendations` | Cost saving recommendations |
| `GET /summary` | Total spend overview |
| `GET /anomalies` | Detected spend anomalies |
| `GET /forecast` | Cost forecast (Prophet ML) |
| `GET /docs` | Interactive Swagger UI |

---

## 💰 Cost Impact

Every Terraform PR automatically shows estimated cost delta via Infracost:
```
Monthly estimate: $142.30
├── aws_eks_cluster:     $72.00
├── aws_instance (x4):   $52.56
└── aws_nat_gateway:     $17.74
```

---

## 📁 Project Structure
```
ai-cost-optimizer/
├── terraform/
│   ├── modules/
│   │   ├── eks/          # EKS cluster + node groups + IRSA
│   │   ├── networking/   # VPC, subnets, NAT, security groups
│   │   └── monitoring/   # Prometheus/Grafana infra
│   └── environments/
│       └── dev/          # Dev environment config
├── k8s/
│   ├── base/             # Kubernetes manifests
│   └── helm-values/      # Prometheus stack config
├── src/
│   └── optimizer/        # Python FastAPI ML engine
├── exporters/
│   └── llm-cost-exporter/ # Custom Prometheus exporter
├── dashboards/grafana/   # Dashboard JSON exports
└── .github/workflows/    # CI/CD pipelines
```

---

## 🔒 Security

- All secrets stored in Kubernetes secrets / AWS Secrets Manager
- IRSA for pod-level AWS permissions (no static credentials)
- Trivy container scanning on every build
- Checkov IaC security scanning
- No hardcoded credentials anywhere in codebase

---

## 📄 License

MIT © 2024 — Built as a production-grade DevOps portfolio project
