# 🚀 Deployment Kubernetes Local

Hướng dẫn đầy đủ để deploy AI Trading System lên local Kubernetes cluster.

## 📋 Yêu cầu

### Bắt buộc
- **Docker Desktop** hoặc **Podman** (với Kubernetes enabled)
- **Minikube** (hoặc sử dụng Docker Desktop Kubernetes)
- **kubectl** (Kubernetes CLI)
- **Git** & **Bash/Shell**

### Cấu hình tối thiểu
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 10 GB free space

### Cài đặt trên Linux
```bash
# Cài Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Cài Minikube
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Cài kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

## 🚀 Bắt đầu nhanh

### 1. Automated Deployment (Khuyến nghị)
```bash
# Chạy script deployment
./deploy-local-k8s.sh

# Script sẽ:
# ✓ Kiểm tra dependencies
# ✓ Start Minikube
# ✓ Build Docker images
# ✓ Deploy all services
# ✓ Hiển thị status
```

### 2. Hoặc Deployment Manual

#### Step 1: Start Minikube
```bash
minikube start --cpus=4 --memory=8192 --driver=docker

# Kiểm tra status
minikube status

# Setup Docker environment
eval $(minikube docker-env)
```

#### Step 2: Build Images
```bash
# Backend (Java Spring Boot)
cd backend
docker build -t ai-trading/orchestrator:latest .
cd ..

# Agents (Python)
docker build -t ai-trading/data-agent:latest ./agents/data_agent
docker build -t ai-trading/analysis-agent:latest ./agents/analysis_agent
docker build -t ai-trading/strategy-agent:latest ./agents/strategy_agent
docker build -t ai-trading/risk-agent:latest ./agents/risk_agent
docker build -t ai-trading/execution-agent:latest ./agents/execution_agent
docker build -t ai-trading/monitoring-agent:latest ./agents/monitoring_agent
```

#### Step 3: Deploy to Kubernetes
```bash
# Tạo namespace
kubectl apply -f infrastructure/kubernetes/namespace.yaml

# Deploy infrastructure (Kafka, Redis, PostgreSQL)
kubectl apply -f infrastructure/kubernetes/infrastructure-deployment.yaml

# Deploy Orchestrator
kubectl apply -f infrastructure/kubernetes/orchestrator-deployment.yaml

# Deploy Agents
kubectl apply -f infrastructure/kubernetes/agents-deployment.yaml

# Deploy ConfigMaps
kubectl apply -f infrastructure/kubernetes/config.yaml
```

#### Step 4: Kiểm tra Status
```bash
# View all resources
kubectl get all -n ai-trading

# View pods
kubectl get pods -n ai-trading

# View services
kubectl get svc -n ai-trading

# View detailed status
kubectl describe pod orchestrator-xxxxx -n ai-trading
```

## 📊 Monitoring & Access

### Port Forwarding

**Orchestrator API:**
```bash
kubectl port-forward -n ai-trading svc/orchestrator 8080:8080
```

**Redis:**
```bash
kubectl port-forward -n ai-trading svc/redis 6379:6379
```

**PostgreSQL:**
```bash
kubectl port-forward -n ai-trading svc/postgres 5432:5432
```

**Kafka:**
```bash
kubectl port-forward -n ai-trading svc/kafka 9092:9092
```

### API Testing
```bash
# Check health
curl http://localhost:8080/api/health

# Get trading signals
curl http://localhost:8080/api/signals

# Submit trading order
curl -X POST http://localhost:8080/api/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC","action":"BUY","quantity":1}'
```

## 📋 Quick Commands

Sử dụng `quick-deploy.sh` để quản lý deployment dễ dàng:

```bash
# Deployment
./quick-deploy.sh deploy

# Check status
./quick-deploy.sh status

# View logs
./quick-deploy.sh logs                 # Orchestrator logs
./quick-deploy.sh logs-agents          # Agent logs

# Port forward
./quick-deploy.sh port-forward

# Get shell access
./quick-deploy.sh shell

# Restart service
./quick-deploy.sh restart

# Cleanup
./quick-deploy.sh clean
```

## 📁 Project Structure

```
infrastructure/kubernetes/
├── namespace.yaml                    # K8s namespace (ai-trading)
├── config.yaml                       # ConfigMap & Secrets
├── orchestrator-deployment.yaml      # Orchestrator pod
├── agents-deployment.yaml            # All AI agents
└── infrastructure-deployment.yaml    # Kafka, Redis, PostgreSQL
```

## 🔍 Troubleshooting

### Pods không khởi động

```bash
# Check events
kubectl describe pod <pod-name> -n ai-trading

# View logs
kubectl logs <pod-name> -n ai-trading --tail=100

# Get previous logs (nếu pod crashed)
kubectl logs <pod-name> -n ai-trading --previous
```

### Image không tìm thấy
```bash
# Verify images exist
docker images | grep ai-trading

# Rebuild nếu cần
docker build -t ai-trading/orchestrator:latest ./backend

# Restart deployment
kubectl rollout restart deployment/orchestrator -n ai-trading
```

### Minikube issues
```bash
# Reset Minikube
minikube delete
minikube start --cpus=4 --memory=8192 --driver=docker

# Check Minikube logs
minikube logs
```

### Xem chi tiết pod
```bash
# Get shell access
kubectl exec -it <pod-name> -n ai-trading -- /bin/sh

# Check environment variables
kubectl exec <pod-name> -n ai-trading -- env

# Check mounted volumes
kubectl exec <pod-name> -n ai-trading -- ls -la /app
```

## 🔄 Cleanup

### Xóa toàn bộ deployment
```bash
# Option 1: Xóa namespace (xóa tất cả resources)
kubectl delete namespace ai-trading

# Option 2: Stop Minikube
minikube stop

# Option 3: Xóa Minikube cluster
minikube delete
```

## 📊 Resource Limits

Mặc định resource requests/limits:

| Component | Request CPU | Request Mem | Limit CPU | Limit Mem |
|-----------|-------------|------------|-----------|-----------|
| Orchestrator | 250m | 512Mi | 500m | 1Gi |
| Analysis Agent | 200m | 512Mi | 500m | 1Gi |
| Data Agent | 100m | 256Mi | 250m | 512Mi |
| Strategy Agent | 100m | 256Mi | 250m | 512Mi |
| Risk Agent | 100m | 256Mi | 250m | 512Mi |
| Kafka | 250m | 512Mi | 500m | 1Gi |
| Redis | 50m | 128Mi | 100m | 256Mi |
| PostgreSQL | 100m | 256Mi | 250m | 512Mi |

## 📝 Cấu hình & Secrets

### Thêm API Keys
```bash
# Edit secrets
kubectl edit secret trading-secrets -n ai-trading

# Hoặc create mới
kubectl create secret generic trading-secrets \
  --from-literal=BINANCE_API_KEY=your-key \
  --from-literal=BINANCE_API_SECRET=your-secret \
  --from-literal=OPENAI_API_KEY=your-openai-key \
  --from-literal=POSTGRES_PASSWORD=trading_pass \
  -n ai-trading
```

### Update ConfigMap
```bash
# Edit config
kubectl edit configmap trading-config -n ai-trading

# Changes take effect on pod restart
kubectl rollout restart deployment/orchestrator -n ai-trading
```

## 🎯 Next Steps

1. **Development**: Modify code & rebuild images
2. **Testing**: Port forward và test APIs
3. **Monitoring**: Setup Prometheus & Grafana
4. **Production**: Migrate to cloud Kubernetes (AWS EKS, GCP GKE, etc.)

## 📞 Hỗ trợ

Nếu gặp vấn đề:

1. Kiểm tra logs: `kubectl logs <pod> -n ai-trading`
2. Describe pod: `kubectl describe pod <pod> -n ai-trading`
3. Check resources: `kubectl top nodes`, `kubectl top pods -n ai-trading`
4. Kiểm tra networking: `kubectl get svc -n ai-trading`

---

**Tạo bởi:** AI Trading Team
**Cập nhật:** March 2026
**License:** MIT
