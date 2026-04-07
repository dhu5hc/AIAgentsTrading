#!/bin/bash

# 🚀 AI Trading System - Local Kubernetes Deployment Script
# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 AI Trading System - K8s Deployment${NC}"
echo -e "${BLUE}========================================${NC}"

# Step 1: Check prerequisites
echo -e "\n${YELLOW}📋 Step 1: Checking prerequisites...${NC}"

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓ $1 found${NC}"
        return 0
    else
        echo -e "${RED}✗ $1 not found. Please install it.${NC}"
        return 1
    fi
}

MISSING_DEPS=0
check_command "docker" || MISSING_DEPS=1
check_command "minikube" || MISSING_DEPS=1
check_command "kubectl" || MISSING_DEPS=1

if [ $MISSING_DEPS -eq 1 ]; then
    echo -e "${RED}Please install missing dependencies${NC}"
    exit 1
fi

# Step 2: Start Minikube
echo -e "\n${YELLOW}🚀 Step 2: Starting Minikube...${NC}"
MINIKUBE_STATUS=$(minikube status 2>/dev/null)
if echo "$MINIKUBE_STATUS" | grep -q "Running"; then
    echo -e "${GREEN}✓ Minikube is already running${NC}"
else
    echo -e "${BLUE}Starting Minikube...${NC}"
    minikube start --cpus=4 --memory=8192 --driver=docker
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to start Minikube${NC}"
        exit 1
    fi
fi

# Step 3: Setup Docker environment
echo -e "\n${YELLOW}🐳 Step 3: Setting up Docker environment...${NC}"
eval $(minikube docker-env)
echo -e "${GREEN}✓ Docker environment configured${NC}"

# Step 4: Build Docker images
echo -e "\n${YELLOW}🔨 Step 4: Building Docker images...${NC}"

build_image() {
    local context=$1
    local tag=$2
    echo -e "${BLUE}Building $tag...${NC}"
    docker build -t $tag $context
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $tag built successfully${NC}"
    else
        echo -e "${RED}✗ Failed to build $tag${NC}"
        return 1
    fi
}

build_image "./backend" "ai-trading/orchestrator:latest" || exit 1
build_image "./agents/data_agent" "ai-trading/data-agent:latest" || exit 1
build_image "./agents/analysis_agent" "ai-trading/analysis-agent:latest" || exit 1
build_image "./agents/strategy_agent" "ai-trading/strategy-agent:latest" || exit 1
build_image "./agents/risk_agent" "ai-trading/risk-agent:latest" || exit 1
build_image "./agents/execution_agent" "ai-trading/execution-agent:latest" || exit 1
build_image "./agents/monitoring_agent" "ai-trading/monitoring-agent:latest" || exit 1

# Step 5: Create namespace
echo -e "\n${YELLOW}🏢 Step 5: Creating Kubernetes namespace...${NC}"
kubectl apply -f infrastructure/kubernetes/namespace.yaml
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Namespace created${NC}"
fi

# Step 6: Create ConfigMap and Secrets
echo -e "\n${YELLOW}🔑 Step 6: Creating ConfigMap and Secrets...${NC}"
kubectl apply -f infrastructure/kubernetes/config.yaml
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ConfigMap and Secrets created${NC}"
fi

# Step 7: Deploy Orchestrator
echo -e "\n${YELLOW}🎯 Step 7: Deploying Orchestrator...${NC}"
kubectl apply -f infrastructure/kubernetes/orchestrator-deployment.yaml
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Orchestrator deployed${NC}"
fi

# Step 8: Deploy Agents
echo -e "\n${YELLOW}🤖 Step 8: Deploying AI Agents...${NC}"
kubectl apply -f infrastructure/kubernetes/agents-deployment.yaml
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ AI Agents deployed${NC}"
fi

# Step 9: Wait for pods to be ready
echo -e "\n${YELLOW}⏳ Step 9: Waiting for pods to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=orchestrator -n ai-trading --timeout=300s 2>/dev/null || true
sleep 5

# Step 10: Display deployment status
echo -e "\n${YELLOW}📊 Step 10: Deployment Status${NC}"
echo -e "${BLUE}Pods:${NC}"
kubectl get pods -n ai-trading

echo -e "\n${BLUE}Services:${NC}"
kubectl get svc -n ai-trading

echo -e "\n${BLUE}Deployments:${NC}"
kubectl get deployments -n ai-trading

# Step 11: Show how to access the system
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Deployment completed successfully!${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${YELLOW}📍 How to access your application:${NC}"
echo ""
echo -e "${BLUE}1. Port forward Orchestrator:${NC}"
echo -e "   ${YELLOW}kubectl port-forward -n ai-trading svc/orchestrator 8080:8080${NC}"
echo ""
echo -e "${BLUE}2. In another terminal, test the API:${NC}"
echo -e "   ${YELLOW}curl http://localhost:8080/api/health${NC}"
echo ""
echo -e "${BLUE}3. View logs:${NC}"
echo -e "   ${YELLOW}kubectl logs -f -n ai-trading -l app=orchestrator${NC}"
echo ""
echo -e "${BLUE}4. Get shell access to a pod:${NC}"
echo -e "   ${YELLOW}kubectl exec -it -n ai-trading <pod-name> -- /bin/sh${NC}"
echo ""
echo -e "${BLUE}5. Delete deployment:${NC}"
echo -e "   ${YELLOW}kubectl delete namespace ai-trading${NC}"
echo ""

echo -e "${YELLOW}📝 For more details, see: DEPLOYMENT_LOCAL_K8S.md${NC}"
