#!/bin/bash

# 🚀 Quick Start - Deploy to Local Kubernetes
# 
# Usage:
#   ./quick-deploy.sh              # Full deployment
#   ./quick-deploy.sh status       # Check status
#   ./quick-deploy.sh logs         # View logs
#   ./quick-deploy.sh clean        # Clean up

NAMESPACE="ai-trading"
COMMAND=${1:-deploy}

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

case $COMMAND in
  deploy)
    echo -e "${BLUE}🚀 Starting deployment...${NC}"
    ./deploy-local-k8s.sh
    ;;
  
  status)
    echo -e "${BLUE}📊 Checking deployment status...${NC}"
    echo -e "\n${YELLOW}Pods:${NC}"
    kubectl get pods -n $NAMESPACE
    echo -e "\n${YELLOW}Services:${NC}"
    kubectl get svc -n $NAMESPACE
    echo -e "\n${YELLOW}Deployments:${NC}"
    kubectl get deployments -n $NAMESPACE
    ;;
  
  logs)
    POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=orchestrator -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -z "$POD_NAME" ]; then
      echo -e "${RED}No orchestrator pod found${NC}"
      exit 1
    fi
    echo -e "${BLUE}📖 Tailing logs from $POD_NAME...${NC}"
    kubectl logs -f -n $NAMESPACE $POD_NAME
    ;;
  
  logs-agents)
    echo -e "${BLUE}📖 Tailing agent logs...${NC}"
    kubectl logs -f -n $NAMESPACE -l app=analysis-agent --tail=50
    ;;
  
  port-forward)
    echo -e "${BLUE}🔗 Port forwarding orchestrator on port 8080...${NC}"
    echo -e "${YELLOW}Access at: http://localhost:8080${NC}"
    kubectl port-forward -n $NAMESPACE svc/orchestrator 8080:8080
    ;;
  
  clean)
    echo -e "${YELLOW}🗑️  Cleaning up namespace ${NC}$NAMESPACE${NC}"
    read -p "Are you sure? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      kubectl delete namespace $NAMESPACE
      echo -e "${GREEN}✓ Namespace deleted${NC}"
    fi
    ;;
  
  shell)
    POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=orchestrator -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -z "$POD_NAME" ]; then
      echo -e "${RED}No orchestrator pod found${NC}"
      exit 1
    fi
    echo -e "${BLUE}📦 Starting shell in $POD_NAME...${NC}"
    kubectl exec -it -n $NAMESPACE $POD_NAME -- /bin/sh
    ;;
  
  restart)
    echo -e "${YELLOW}🔄 Restarting orchestrator...${NC}"
    kubectl rollout restart deployment/orchestrator -n $NAMESPACE
    kubectl rollout status deployment/orchestrator -n $NAMESPACE
    echo -e "${GREEN}✓ Restarted${NC}"
    ;;
  
  *)
    echo -e "${YELLOW}AI Trading System - Quick Deploy Commands${NC}"
    echo ""
    echo -e "${BLUE}Usage:${NC}"
    echo -e "  ${GREEN}./quick-deploy.sh${NC} [command]"
    echo ""
    echo -e "${BLUE}Commands:${NC}"
    echo -e "  ${GREEN}deploy${NC}          - Full deployment (default)"
    echo -e "  ${GREEN}status${NC}          - Check pod and service status"
    echo -e "  ${GREEN}logs${NC}            - View orchestrator logs"
    echo -e "  ${GREEN}logs-agents${NC}     - View agent logs"
    echo -e "  ${GREEN}port-forward${NC}    - Port forward to localhost:8080"
    echo -e "  ${GREEN}shell${NC}           - Get shell access to orchestrator"
    echo -e "  ${GREEN}restart${NC}         - Restart orchestrator"
    echo -e "  ${GREEN}clean${NC}           - Delete namespace and cleanup"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo -e "  ${YELLOW}./quick-deploy.sh deploy${NC}"
    echo -e "  ${YELLOW}./quick-deploy.sh status${NC}"
    echo -e "  ${YELLOW}./quick-deploy.sh logs${NC}"
    ;;
esac
