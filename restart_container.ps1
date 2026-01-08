# Restart Container Script for Windows PowerShell
# This script performs a complete clean rebuild of all Docker containers and images

param(
    [switch]$Volumes,
    [switch]$Images,
    [switch]$All,
    [switch]$Force,
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\restart_container.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Volumes     Remove volumes (database data will be lost!)"
    Write-Host "  -Images      Remove images (full rebuild from Dockerfiles)"
    Write-Host "  -All         Remove volumes AND images (most aggressive)"
    Write-Host "  -Force       Skip confirmation prompts"
    Write-Host "  -Help        Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\restart_container.ps1              # Quick restart (keeps volumes and images)"
    Write-Host "  .\restart_container.ps1 -Volumes     # Remove volumes (database will be reset)"
    Write-Host "  .\restart_container.ps1 -Images      # Remove images (full rebuild)"
    Write-Host "  .\restart_container.ps1 -All         # Complete clean (removes everything)"
    exit 0
}

# Set flags
if ($All) {
    $Volumes = $true
    $Images = $true
}

# Confirmation prompt (unless -Force)
if (-not $Force) {
    if ($Volumes -or $Images) {
        Write-Host "⚠️  WARNING: This will remove Docker resources!" -ForegroundColor Yellow
        if ($Volumes) {
            Write-Host "   - Volumes will be removed (database data will be lost!)" -ForegroundColor Red
        }
        if ($Images) {
            Write-Host "   - Images will be removed (full rebuild required)" -ForegroundColor Red
        }
        Write-Host ""
        $confirm = Read-Host "Are you sure you want to continue? (yes/no)"
        if ($confirm -ne "yes") {
            Write-Host "Aborted."
            exit 1
        }
    }
}

# Step 1: Stop and remove containers
Write-Host "📦 Step 1: Stopping and removing containers..." -ForegroundColor Green
docker-compose down --remove-orphans
Write-Host ""

# Step 2: Remove volumes (if requested)
if ($Volumes) {
    Write-Host "🗑️  Step 2: Removing volumes..." -ForegroundColor Green
    docker-compose down -v
    Write-Host "Volumes removed."
    Write-Host ""
} else {
    Write-Host "📦 Step 2: Keeping volumes (database data preserved)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 3: Remove images (if requested)
if ($Images) {
    Write-Host "🖼️  Step 3: Removing images..." -ForegroundColor Green
    
    # Get image names from docker-compose
    $imageOutput = docker-compose config --images 2>$null
    if ($imageOutput) {
        $images = $imageOutput -split "`n" | Where-Object { $_.Trim() -ne "" }
        foreach ($image in $images) {
            docker rmi -f $image.Trim() 2>$null
        }
    }
    
    Write-Host "Images removed."
    Write-Host ""
} else {
    Write-Host "🖼️  Step 3: Keeping images (will use cached layers if available)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 4: Clean up unused Docker resources
Write-Host "🧹 Step 4: Cleaning up unused Docker resources..." -ForegroundColor Green
docker system prune -f
Write-Host ""

# Step 5: Rebuild images
Write-Host "🔨 Step 5: Rebuilding images..." -ForegroundColor Green
docker-compose build --no-cache
Write-Host ""

# Step 6: Start containers
Write-Host "🚀 Step 6: Starting containers..." -ForegroundColor Green
docker-compose up -d
Write-Host ""

# Step 7: Show status
Write-Host "✅ Containers restarted!" -ForegroundColor Green
Write-Host ""
Write-Host "Container status:"
docker-compose ps
Write-Host ""

# Step 8: Show logs (tail)
Write-Host "📋 Recent logs (last 20 lines):" -ForegroundColor Green
docker-compose logs --tail=20
Write-Host ""

Write-Host "✨ Done!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Initialize database: docker-compose exec backend alembic upgrade head"
Write-Host "  2. Create demo user: docker-compose exec backend python scripts/seed_default_user.py"
Write-Host "  3. View logs: docker-compose logs -f"
Write-Host "  4. Stop containers: docker-compose down"
Write-Host ""
Write-Host "Services available at:"
Write-Host "  - Frontend: http://localhost:3000"
Write-Host "  - Backend API: http://localhost:8000"
Write-Host "  - API Docs: http://localhost:8000/docs"
Write-Host ""
