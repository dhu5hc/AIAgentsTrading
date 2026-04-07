#!/bin/bash

# 🔧 Setup Kubernetes Environment
# Run this script once to prepare your system for local Kubernetes deployment

set -e  # Exit on error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔧 Kubernetes Environment Setup${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to check and report
check_and_install() {
    local cmd=$1
    local install_cmd=$2
    local description=$3

    echo -e "\n${YELLOW}Checking ${description}...${NC}"
    
    if command -v $cmd &> /dev/null; then
        version=$($cmd --version 2>/dev/null | head -n 1 || $cmd version 2>/dev/null | head -n 1)
        echo -e "${GREEN}✓ $description found${NC}"
        echo "  $version"
        return 0
    else
        echo -e "${RED}✗ $cmd not found${NC}"
        echo -e "${YELLOW}To install: $install_cmd${NC}"
        return 1
    fi
}

# Check prerequisites
echo -e "\n${BLUE}1️⃣  Checking Prerequisites${NC}"

MISSING=0

check_and_install "docker" "https://docs.docker.com/get-docker/" "Docker" || MISSING=1
check_and_install "minikube" "curl https://minikube.sigs.k8s.io/docs/start/" "Minikube" || MISSING=1
check_and_install "kubectl" "curl -LO https://dl.k8s.io/release/stable.txt && curl -LO https://dl.k8s.io/release/v1.X/bin/linux/amd64/kubectl" "kubectl" || MISSING=1
check_and_install "git" "apt-get install git (Linux) or brew install git (Mac)" "Git" || MISSING=1

if [ $MISSING -eq 1 ]; then
    echo -e "\n${RED}❌ Please install missing prerequisites${NC}"
    exit 1
fi

echo -e "\n${BLUE}2️⃣  Configuring Docker (Linux only)${NC}"

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! groups | grep -q docker; then
        echo -e "${YELLOW}Adding user to docker group...${NC}"
        sudo usermod -aG docker $USER
        echo -e "${GREEN}✓ User added to docker group${NC}"
        echo -e "${YELLOW}⚠️  You need to log out and log back in for this to take effect${NC}"
    else
        echo -e "${GREEN}✓ User already in docker group${NC}"
    fi
fi

# Check Minikube
echo -e "\n${BLUE}3️⃣  Checking Minikube Status${NC}"

if minikube status &>/dev/null; then
    echo -e "${GREEN}✓ Minikube is running${NC}"
    minikube status
else
    echo -e "${YELLOW}Starting Minikube...${NC}"
    minikube start --cpus=4 --memory=8192 --driver=docker
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Minikube started successfully${NC}"
    else
        echo -e "${RED}✗ Failed to start Minikube${NC}"
        echo -e "${YELLOW}Troubleshooting tips:${NC}"
        echo "  1. Make sure Docker daemon is running"
        echo "  2. Try: minikube delete && minikube start"
        echo "  3. Check: minikube logs"
        exit 1
    fi
fi

# Setup Docker environment
echo -e "\n${BLUE}4️⃣  Setting up Docker Environment${NC}"
eval $(minikube docker-env)
echo -e "${GREEN}✓ Docker environment configured${NC}"

# Test Docker connectivity
echo -e "\n${BLUE}5️⃣  Testing Docker Connectivity${NC}"
docker ps > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker is accessible${NC}"
else
    echo -e "${RED}✗ Cannot connect to Docker${NC}"
    echo -e "${YELLOW}Try: eval \$(minikube docker-env)${NC}"
    exit 1
fi

# Test kubectl connectivity
echo -e "\n${BLUE}6️⃣  Testing Kubernetes Connectivity${NC}"
if kubectl cluster-info &>/dev/null; then
    echo -e "${GREEN}✓ kubectl is connected to Kubernetes${NC}"
    kubectl version --short
else
    echo -e "${RED}✗ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

# Check available resources
echo -e "\n${BLUE}7️⃣  Checking Available Resources${NC}"
echo -e "${YELLOW}Nodes:${NC}"
kubectl get nodes

echo -e "\n${YELLOW}Node resources:${NC}"
kubectl describe nodes | grep -A 5 "Allocated resources"

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Environment setup completed!${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${YELLOW}📝 Next Steps:${NC}"
echo ""
echo -e "  1. ${GREEN}Build Docker images:${NC}"
echo -e "     ${YELLOW}cd backend && docker build -t ai-trading/orchestrator:latest .${NC}"
echo ""
echo -e "  2. ${GREEN}Deploy to Kubernetes:${NC}"
echo -e "     ${YELLOW}./deploy-local-k8s.sh${NC}"
echo ""
echo -e "  3. ${GREEN}Or use quick commands:${NC}"
echo -e "     ${YELLOW}./quick-deploy.sh status${NC}"
echo ""

echo -e "${YELLOW}📚 For detailed instructions, see:${NC}"
echo "  - K8S_DEPLOYMENT.md"
echo "  - DEPLOYMENT_LOCAL_K8S.md"
echo ""

echo -e "${YELLOW}💡 Useful commands:${NC}"
echo "  - ${YELLOW}minikube status${NC}          - Check Minikube status"
echo "  - ${YELLOW}minikube logs${NC}            - View Minikube logs"
echo "  - ${YELLOW}minikube dashboard${NC}       - Open Kubernetes dashboard"
echo "  - ${YELLOW}kubectl get all -n ai-trading${NC}  - View all resources"
echo ""
