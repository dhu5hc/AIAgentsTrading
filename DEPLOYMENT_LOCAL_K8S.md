# 📦 Hướng dẫn Deploy lên Local Kubernetes

Hướng dẫn này sẽ giúp bạn deploy AI Trading System lên local Kubernetes (sử dụng Minikube).

## 📋 Yêu cầu

- Docker Desktop hoặc Podman
- Minikube (hoặc Docker Desktop with Kubernetes enabled)
- kubectl
- Git

## 🚀 Cài đặt & Deploy

### 1️⃣ Chuẩn bị Minikube

```bash
# Kiểm tra nếu Minikube đã cài
minikube version

# Start Minikube (nếu chưa chạy)
minikube start --cpus=4 --memory=8192 --driver=docker

# Enable Docker addon để pull images
eval $(minikube docker-env)
```

### 2️⃣ Build Docker Images

```bash
# Build orchestrator image
cd backend
docker build -t ai-trading/orchestrator:latest .
cd ..

# Build agent images
docker build -t ai-trading/data-agent:latest ./agents/data_agent
docker build -t ai-trading/analysis-agent:latest ./agents/analysis_agent
docker build -t ai-trading/strategy-agent:latest ./agents/strategy_agent
docker build -t ai-trading/risk-agent:latest ./agents/risk_agent
docker build -t ai-trading/execution-agent:latest ./agents/execution_agent
docker build -t ai-trading/monitoring-agent:latest ./agents/monitoring_agent
```

### 3️⃣ Tạo Namespace & ConfigMaps

```bash
# Tạo namespace
kubectl apply -f infrastructure/kubernetes/namespace.yaml

# Tạo ConfigMap và Secret
kubectl apply -f infrastructure/kubernetes/config.yaml

# Nếu cần update API keys, chỉnh sửa Secret
kubectl edit secret trading-secrets -n ai-trading
```

### 4️⃣ Deploy các services

```bash
# Deploy Orchestrator
kubectl apply -f infrastructure/kubernetes/orchestrator-deployment.yaml

# Deploy Agents
kubectl apply -f infrastructure/kubernetes/agents-deployment.yaml

# Deploy Config (Kafka, Redis, PostgreSQL)
kubectl apply -f infrastructure/kubernetes/config.yaml
```

### 5️⃣ Kiểm tra Status

```bash
# Xem tất cả pods
kubectl get pods -n ai-trading

# Xem chi tiết pod cụ thể
kubectl describe pod orchestrator-xxxxx -n ai-trading

# Xem logs
kubectl logs -f orchestrator-xxxxx -n ai-trading
```

### 6️⃣ Port Forward để Access

```bash
# Orchestrator API
kubectl port-forward -n ai-trading svc/orchestrator 8080:8080

# Trong terminal khác:
curl http://localhost:8080/api/health
```

## 📊 Monitoring

### Prometheus & Grafana

```bash
# Deploy Prometheus
kubectl apply -f infrastructure/prometheus/prometheus.yml

# Port forward Prometheus
kubectl port-forward -n ai-trading svc/prometheus 9090:9090
```

## 🛠️ Troubleshooting

### Pod không khởi động?
```bash
# Kiểm tra events
kubectl describe pod <pod-name> -n ai-trading

# Xem chi tiết logs
kubectl logs <pod-name> -n ai-trading --tail=50
```

### Lỗi image không tìm thấy?
```bash
# Kiểm tra images có sẵn
docker images | grep ai-trading

# Hoặc rebuild
docker build -t ai-trading/orchestrator:latest ./backend
```

### Cần xóa và deploy lại?
```bash
# Xóa deployment
kubectl delete namespace ai-trading

# Deploy lại từ đầu
kubectl apply -f infrastructure/kubernetes/namespace.yaml
kubectl apply -f infrastructure/kubernetes/config.yaml
kubectl apply -f infrastructure/kubernetes/orchestrator-deployment.yaml
kubectl apply -f infrastructure/kubernetes/agents-deployment.yaml
```

## 📝 Ghi chú

- Local Kubernetes sử dụng `imagePullPolicy: IfNotPresent` để dùng local images
- Cần cấu hình API keys trong Secret nếu muốn kết nối thực tế với Binance, OpenAI, etc.
- Mặc định deploy ở namespace `ai-trading`

## 📞 Hỗ trợ

Nếu gặp vấn đề, kiểm tra:
- Docker daemon đang chạy?
- Minikube status: `minikube status`
- Sufficient resources: `minikube config view`
