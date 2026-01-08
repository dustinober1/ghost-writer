#!/bin/bash

# Restart Container Script
# This script performs a complete clean rebuild of all Docker containers and images

set -e  # Exit on any error

echo "🚀 Starting complete container restart..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse command line arguments
REMOVE_VOLUMES=false
REMOVE_IMAGES=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--volumes)
            REMOVE_VOLUMES=true
            shift
            ;;
        -i|--images)
            REMOVE_IMAGES=true
            shift
            ;;
        -a|--all)
            REMOVE_VOLUMES=true
            REMOVE_IMAGES=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --volumes    Remove volumes (database data will be lost!)"
            echo "  -i, --images     Remove images (full rebuild from Dockerfiles)"
            echo "  -a, --all        Remove volumes AND images (most aggressive)"
            echo "  -f, --force      Skip confirmation prompts"
            echo "  -h, --help       Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                # Quick restart (keeps volumes and images)"
            echo "  $0 -v             # Remove volumes (database will be reset)"
            echo "  $0 -i             # Remove images (full rebuild)"
            echo "  $0 -a             # Complete clean (removes everything)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Confirmation prompt (unless --force)
if [ "$FORCE" = false ]; then
    if [ "$REMOVE_VOLUMES" = true ] || [ "$REMOVE_IMAGES" = true ]; then
        echo -e "${YELLOW}⚠️  WARNING: This will remove Docker resources!${NC}"
        if [ "$REMOVE_VOLUMES" = true ]; then
            echo -e "${RED}   - Volumes will be removed (database data will be lost!)${NC}"
        fi
        if [ "$REMOVE_IMAGES" = true ]; then
            echo -e "${RED}   - Images will be removed (full rebuild required)${NC}"
        fi
        echo ""
        read -p "Are you sure you want to continue? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo "Aborted."
            exit 1
        fi
    fi
fi

# Step 1: Stop and remove containers
echo -e "${GREEN}📦 Step 1: Stopping and removing containers...${NC}"
docker-compose down --remove-orphans
echo ""

# Step 2: Remove volumes (if requested)
if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "${GREEN}🗑️  Step 2: Removing volumes...${NC}"
    docker-compose down -v
    echo "Volumes removed."
    echo ""
else
    echo -e "${YELLOW}📦 Step 2: Keeping volumes (database data preserved)${NC}"
    echo ""
fi

# Step 3: Remove images (if requested)
if [ "$REMOVE_IMAGES" = true ]; then
    echo -e "${GREEN}🖼️  Step 3: Removing images...${NC}"
    
    # Get image names from docker-compose
    IMAGES=$(docker-compose config --images 2>/dev/null || echo "")
    
    if [ -n "$IMAGES" ]; then
        echo "Removing project images..."
        echo "$IMAGES" | xargs -r docker rmi -f 2>/dev/null || true
    fi
    
    echo "Images removed."
    echo ""
else
    echo -e "${YELLOW}🖼️  Step 3: Keeping images (will use cached layers if available)${NC}"
    echo ""
fi

# Step 4: Clean up unused Docker resources
echo -e "${GREEN}🧹 Step 4: Cleaning up unused Docker resources...${NC}"
docker system prune -f
echo ""

# Step 5: Rebuild images
echo -e "${GREEN}🔨 Step 5: Rebuilding images...${NC}"
docker-compose build --no-cache
echo ""

# Step 6: Start containers
echo -e "${GREEN}🚀 Step 6: Starting containers...${NC}"
docker-compose up -d
echo ""

# Step 7: Show status
echo -e "${GREEN}✅ Containers restarted!${NC}"
echo ""
echo "Container status:"
docker-compose ps
echo ""

# Step 8: Show logs (tail)
echo -e "${GREEN}📋 Recent logs (last 20 lines):${NC}"
docker-compose logs --tail=20
echo ""

echo -e "${GREEN}✨ Done!${NC}"
echo ""
echo "Next steps:"
echo "  1. Initialize database: docker-compose exec backend alembic upgrade head"
echo "  2. Create demo user: docker-compose exec backend python scripts/seed_default_user.py"
echo "  3. View logs: docker-compose logs -f"
echo "  4. Stop containers: docker-compose down"
echo ""
echo "Services available at:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
