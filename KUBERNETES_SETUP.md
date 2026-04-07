# 🚀 Deployment Kubernetes - Complete Setup Guide

> **Hệ thống Trading AI được chuẩn bị sẵn sàng để deploy lên local Kubernetes**

## 📚 Tài liệu

Dưới đây là toàn bộ hướng dẫn và công cụ để deploy ứng dụng:

### 📖 Hướng dẫn Chi Tiết
1. **[K8S_DEPLOYMENT.md](K8S_DEPLOYMENT.md)** ⭐ **BẮT ĐẦU TỪ ĐÂY**
   - Hướng dẫn đầy đủ (tiếng Việt)
   - Yêu cầu hệ thống
   - Deploy manual hoặc automated
   - Troubleshooting

2. **[DEPLOYMENT_LOCAL_K8S.md](DEPLOYMENT_LOCAL_K8S.md)**
   - Hướng dẫn nhanh
   - Các lệnh cơ bản
   - Port forwarding
   - Cleanup

3. **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)**
   - Danh sách files đã tạo
   - Quick start

## 🛠️ Scripts Tự động

### 1. Setup môi trường (Lần đầu)
```bash
./setup-k8s-env.sh
```
- ✅ Kiểm tra Docker, Minikube, kubectl
- ✅ Start Minikube
- ✅ Configure Docker environment
- ✅ Test kết nối

### 2. Deploy toàn bộ hệ thống (Khuyến nghị)
```bash
./deploy-local-k8s.sh
```
Tự động thực hiện:
- ✅ Build tất cả Docker images
- ✅ Tạo Kubernetes namespace
- ✅ Deploy Orchestrator
- ✅ Deploy tất cả Agents
- ✅ Deploy infrastructure (Kafka, Redis, PostgreSQL)
- ✅ Hiển thị status

### 3. Quản lý deployment (Quick commands)
```bash
# Kiểm tra status
./quick-deploy.sh status

# Xem logs
./quick-deploy.sh logs

# Port forward
./quick-deploy.sh port-forward

# Get shell
./quick-deploy.sh shell

# Restart
./quick-deploy.sh restart

# Cleanup
./quick-deploy.sh clean
```

## ⚡ Quick Start (5 phút)

### Bước 1: Cài đặt môi trường
```bash
./setup-k8s-env.sh
```

### Bước 2: Deploy
```bash
./deploy-local-k8s.sh
```

### Bước 3: Kiểm tra
```bash
./quick-deploy.sh status
```

### Bước 4: Test API
```bash
# Terminal 1: Port forward
./quick-deploy.sh port-forward

# Terminal 2: Test
curl http://localhost:8080/api/health
```

## 📦 Các Thành phần Được Deploy

### Java Services
- **Orchestrator** - Spring Boot API (Port 8080)
  - REST endpoints cho trading
  - Health checks
  - Coordination

### Python Agents
- **Data Agent** - Thu thập dữ liệu
- **Analysis Agent** - Phân tích thị trường
- **Strategy Agent** - Quyết định trading
- **Risk Agent** - Quản lý rủi ro
- **Execution Agent** - Thực thi lệnh
- **Monitoring Agent** - Giám sát hệ thống

### Infrastructure
- **Kafka** - Message broker
- **Redis** - Cache & real-time data
- **PostgreSQL** - Database

## 🔧 System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Disk | 10 GB | 20+ GB |
| Docker | Latest | Latest |
| Minikube | Latest | Latest |
| kubectl | Latest | Latest |

## 📊 Project Structure

```
AIAgentsTrading/
├── 📖 Documentation
│   ├── K8S_DEPLOYMENT.md              ⭐ START HERE
│   ├── DEPLOYMENT_LOCAL_K8S.md
│   └── DEPLOYMENT_SUMMARY.md
│
├── 🛠️ Deployment Scripts
│   ├── setup-k8s-env.sh               # Environment setup
│   ├── deploy-local-k8s.sh            # Full deployment
│   └── quick-deploy.sh                # Quick commands
│
├── 📦 Kubernetes Manifests
│   └── infrastructure/kubernetes/
│       ├── namespace.yaml
│       ├── config.yaml
│       ├── orchestrator-deployment.yaml
│       ├── agents-deployment.yaml
│       └── infrastructure-deployment.yaml
│
├── 🐳 Docker Configurations
│   ├── backend/Dockerfile
│   ├── agents/data_agent/Dockerfile
│   ├── agents/analysis_agent/Dockerfile
│   ├── agents/strategy_agent/Dockerfile
│   ├── agents/risk_agent/Dockerfile
│   ├── agents/execution_agent/Dockerfile
│   └── agents/monitoring_agent/Dockerfile
│
└── 📄 Source Code
    ├── backend/                       # Java Spring Boot
    └── agents/                        # Python agents
```

## 🎯 Common Tasks

### Xem trạng thái
```bash
kubectl get all -n ai-trading
```

### Xem logs
```bash
kubectl logs -f -n ai-trading deployment/orchestrator
```

### Truy cập container
```bash
./quick-deploy.sh shell
```

### Port forward
```bash
./quick-deploy.sh port-forward
```

### Restart service
```bash
./quick-deploy.sh restart
```

### Xóa deployment
```bash
./quick-deploy.sh clean
```

## 🐛 Troubleshooting

### Pod không khởi động?
```bash
./quick-deploy.sh logs
kubectl describe pod <pod-name> -n ai-trading
```

### Image không tìm?
```bash
docker build -t ai-trading/orchestrator:latest ./backend
./quick-deploy.sh restart
```

### Minikube issues?
```bash
minikube delete
minikube start --cpus=4 --memory=8192 --driver=docker
```

## 📞 Getting Help

1. Kiểm tra logs:
   ```bash
   ./quick-deploy.sh logs
   ```

2. Xem chi tiết pod:
   ```bash
   kubectl describe pod <pod-name> -n ai-trading
   ```

3. Đọc hướng dẫn:
   ```bash
   # Chi tiết
   cat K8S_DEPLOYMENT.md
   
   # Nhanh
   cat DEPLOYMENT_LOCAL_K8S.md
   ```

## ✅ Checklist

- [ ] Docker installed & running
- [ ] Minikube installed
- [ ] kubectl installed
- [ ] Run `./setup-k8s-env.sh`
- [ ] Run `./deploy-local-k8s.sh`
- [ ] Check status: `./quick-deploy.sh status`
- [ ] Port forward: `./quick-deploy.sh port-forward`
- [ ] Test API: `curl http://localhost:8080/api/health`

## 🚀 Next Steps

1. **Development**: Modify code locally
2. **Testing**: Test via API
3. **Monitoring**: Setup dashboards
4. **Production**: Deploy to cloud (AWS EKS, GCP GKE, etc.)

---

**Status**: ✅ Ready to Deploy  
**Last Updated**: March 27, 2026  
**Version**: 1.0
