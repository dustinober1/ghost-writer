#!/bin/bash

# Improved Container Restart Script
# This script efficiently rebuilds only changed services using Docker cache

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
REBUILD_ALL=false
REBUILD_BACKEND=false
REBUILD_FRONTEND=false
FORCE=false
QUIET=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--backend)
            REBUILD_BACKEND=true
            shift
            ;;
        -f|--frontend)
            REBUILD_FRONTEND=true
            shift
            ;;
        -a|--all)
            REBUILD_ALL=true
            shift
            ;;
        -y|--yes)
            FORCE=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Efficiently restart containers, only rebuilding changed services using Docker cache."
            echo ""
            echo "Options:"
            echo "  -b, --backend      Force rebuild backend service"
            echo "  -f, --frontend     Force rebuild frontend service"
            echo "  -a, --all          Force rebuild all services (ignores cache)"
            echo "  -y, --yes          Skip confirmation prompts"
            echo "  -q, --quiet         Suppress verbose output"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                  # Smart rebuild (only changed services)"
            echo "  $0 -b              # Rebuild backend"
            echo "  $0 -f              # Rebuild frontend"
            echo "  $0 -a              # Rebuild everything (no cache)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Function to check if files changed
check_files_changed() {
    local service=$1
    local last_modified_file=".docker_${service}_last_modified"
    
    if [ ! -f "$last_modified_file" ]; then
        touch "$last_modified_file"
        return 0  # First run, assume changed
    fi
    
    local last_modified=$(cat "$last_modified_file")
    
    if [ "$service" = "backend" ]; then
        # Check if backend files changed
        find backend/app backend/requirements.txt backend/Dockerfile -newer "$last_modified_file" 2>/dev/null | grep -q . && return 0
    elif [ "$service" = "frontend" ]; then
        # Check if frontend files changed
        find frontend/src frontend/package.json frontend/Dockerfile frontend/vite.config.ts -newer "$last_modified_file" 2>/dev/null | grep -q . && return 0
    fi
    
    return 1  # No changes detected
}

# Step 1: Check what changed
if [ "$REBUILD_ALL" = false ]; then
    [ "$QUIET" = false ] && echo -e "${BLUE}🔍 Step 1: Checking for changed files...${NC}"
    
    backend_changed=false
    frontend_changed=false
    
    if [ "$REBUILD_BACKEND" = true ] || check_files_changed "backend"; then
        backend_changed=true
    fi
    
    if [ "$REBUILD_FRONTEND" = true ] || check_files_changed "frontend"; then
        frontend_changed=true
    fi
    
    [ "$QUIET" = false ] && echo ""
else
    [ "$QUIET" = false ] && echo -e "${YELLOW}⚠️  Force rebuild all services (--all)${NC}"
    backend_changed=true
    frontend_changed=true
fi

# Step 2: Stop containers
[ "$QUIET" = false ] && echo -e "${GREEN}📦 Step 2: Stopping containers...${NC}"
docker-compose down

# Step 3: Clean up (optional, with cache preservation)
if [ "$backend_changed" = false ] && [ "$frontend_changed" = false ]; then
    [ "$QUIET" = false ] && echo -e "${YELLOW}ℹ️  No changes detected - starting existing containers...${NC}"
fi

# Step 4: Rebuild changed services (with cache)
if [ "$backend_changed" = true ] || [ "$frontend_changed" = true ] || [ "$REBUILD_ALL" = true ]; then
    [ "$QUIET" = false ] && echo -e "${GREEN}🔨 Step 3: Rebuilding services (using Docker cache)...${NC}"
    
    if [ "$REBUILD_ALL" = true ]; then
        # Full rebuild without cache
        docker-compose build --no-cache
    else
        # Smart rebuild - only changed services use cache
        build_flags=""
        
        if [ "$backend_changed" = true ] && [ "$frontend_changed" = false ]; then
            build_flags="backend"
        elif [ "$backend_changed" = false ] && [ "$frontend_changed" = true ]; then
            build_flags="frontend"
        else
            # Both changed, rebuild all but with cache
            build_flags=""
        fi
        
        if [ -n "$build_flags" ]; then
            docker-compose build $build_flags
        else
            docker-compose build
        fi
    fi
    
    # Update modification timestamps
    if [ "$backend_changed" = true ]; then
        touch .docker_backend_last_modified
    fi
    if [ "$frontend_changed" = true ]; then
        touch .docker_frontend_last_modified
    fi
fi

# Step 5: Start containers
[ "$QUIET" = false ] && echo -e "${GREEN}🚀 Step 4: Starting containers...${NC}"
docker-compose up -d

# Wait for services to be healthy
[ "$QUIET" = false ] && echo -e "${BLUE}⏳ Step 5: Waiting for services to be healthy...${NC}"

# Simple health check loop
max_attempts=30
attempt=0
healthy_count=0

while [ $attempt -lt $max_attempts ]; do
    backend_status=$(docker-compose ps -q backend 2>/dev/null || echo "not found")
    frontend_status=$(docker-compose ps -q frontend 2>/dev/null || echo "not found")
    
    if [[ "$backend_status" == *"healthy"* ]] || [[ "$backend_status" == *"Up"* ]]; then
        ((healthy_count++))
    fi
    
    if [[ "$frontend_status" == *"healthy"* ]] || [[ "$frontend_status" == *"Up"* ]]; then
        ((healthy_count++))
    fi
    
    if [ $healthy_count -ge 2 ]; then
        [ "$QUIET" = false ] && echo -e "${GREEN}✅ All services healthy!${NC}"
        break
    fi
    
    sleep 1
    ((attempt++))
done

if [ $attempt -ge $max_attempts ]; then
    [ "$QUIET" = false ] && echo -e "${YELLOW}⚠️  Services started but health check timed out${NC}"
    [ "$QUIET" = false ] && echo -e "${YELLOW}ℹ️  Check container status with: docker-compose ps${NC}"
fi

# Show summary
[ "$QUIET" = false ] && echo ""
[ "$QUIET" = false ] && echo -e "${GREEN}✨ Done!${NC}"
[ "$QUIET" = false ] && echo ""
[ "$QUIET" = false ] && echo "Container status:"
docker-compose ps
[ "$QUIET" = false ] && echo ""
[ "$QUIET" = false ] && echo "Services available at:"
[ "$QUIET" = false ] && echo "  - Frontend: http://localhost:3000"
[ "$QUIET" = false ] && echo "  - Backend API: http://localhost:8000"
[ "$QUIET" = false ] && echo "  - API Docs: http://localhost:8000/docs"
[ "$QUIET" = false ] && echo ""
[ "$QUIET" = false ] && echo "View logs: docker-compose logs -f"
[ "$QUIET" = false ] && echo "Stop containers: docker-compose down"
