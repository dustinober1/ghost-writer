# Docker Setup Guide

Run the entire Ghostwriter application with a single command using Docker Compose.

## Quick Start

### Development Mode (with hot reload)

```bash
docker-compose up
```

This starts:
- **PostgreSQL** on port 5432
- **Backend API** on port 8000
- **Frontend** on port 3000

### Production Mode

```bash
docker-compose -f docker-compose.prod.yml up -d
```

This starts:
- **PostgreSQL** on port 5432
- **Backend API** on port 8000
- **Frontend** on port 80 (nginx)

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- At least 4GB RAM available
- Ports 3000, 8000, and 5432 available

## First Time Setup

### 1. Create Environment File

Create a `.env` file in the project root (optional, for custom configuration):

```bash
# Database
POSTGRES_USER=ghostwriter
POSTGRES_PASSWORD=ghostwriter_password
POSTGRES_DB=ghostwriter

# Backend
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
DEFAULT_LLM_MODEL=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama2
```

### 2. Start All Services

```bash
docker-compose up --build
```

The `--build` flag rebuilds images on first run.

### 3. Initialize Database

In a new terminal, run migrations:

```bash
docker-compose exec backend alembic upgrade head
```

### 4. Create Default User (Optional)

```bash
docker-compose exec backend python scripts/seed_default_user.py
```

## Accessing the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432

## Default Credentials

After seeding the default user:
- **Email**: `demo@ghostwriter.com`
- **Password**: `demo123`

## Useful Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Stop Services

```bash
docker-compose down
```

### Stop and Remove Volumes (Clean Slate)

```bash
docker-compose down -v
```

### Restart a Service

```bash
docker-compose restart backend
docker-compose restart frontend
```

### Execute Commands in Containers

```bash
# Backend shell
docker-compose exec backend bash

# Run Python script
docker-compose exec backend python scripts/seed_default_user.py

# Database shell
docker-compose exec postgres psql -U ghostwriter -d ghostwriter
```

### Rebuild After Code Changes

```bash
# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Rebuild all
docker-compose build
docker-compose up -d
```

## Development vs Production

### Development (`docker-compose.yml`)
- Hot reload enabled
- Source code mounted as volumes
- Frontend uses Vite dev server
- Backend uses uvicorn with --reload

### Production (`docker-compose.prod.yml`)
- Optimized builds
- Frontend served via nginx
- No source code volumes
- Production-ready configuration

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :3000
lsof -i :8000
lsof -i :5432

# Change ports in docker-compose.yml
ports:
  - "3001:3000"  # Use 3001 instead of 3000
```

### Database Connection Issues

```bash
# Check if postgres is healthy
docker-compose ps

# View postgres logs
docker-compose logs postgres

# Test connection
docker-compose exec backend python -c "from app.models.database import engine; engine.connect()"
```

### Frontend Can't Connect to Backend

1. Check backend is running: `docker-compose ps`
2. Check backend logs: `docker-compose logs backend`
3. Verify API is accessible: `curl http://localhost:8000/health`
4. Check browser console for CORS errors

### Out of Memory

If you get out of memory errors:
1. Increase Docker memory limit in Docker Desktop settings
2. Or use smaller ML models
3. Or run services separately instead of all at once

### Complete Clean Restart

**Quick restart** (keeps volumes and images):
```bash
./restart_container.sh
```

**Remove volumes** (database will be reset):
```bash
./restart_container.sh -v
```

**Complete clean** (removes volumes and images, full rebuild):
```bash
./restart_container.sh -a
```

**Skip confirmation prompts**:
```bash
./restart_container.sh -a -f
```

**Windows PowerShell**:
```powershell
.\restart_container.ps1 -All
```

**Using Makefile**:
```bash
make restart        # Quick restart
make restart-clean  # Remove volumes
make restart-all    # Complete clean
```

The restart script will:
1. Stop and remove containers
2. Optionally remove volumes and images
3. Clean up unused Docker resources
4. Rebuild images from scratch
5. Start containers
6. Show status and logs

**Manual rebuild** (alternative):
```bash
# Stop and remove everything
docker-compose down -v

# Remove images
docker-compose rm -f

# Rebuild from scratch
docker-compose build --no-cache

# Start fresh
docker-compose up
```

## Environment Variables

You can override defaults by creating a `.env` file in the project root:

```bash
# .env
SECRET_KEY=your-secret-key
POSTGRES_PASSWORD=your-password
OPENAI_API_KEY=your-key
```

## Volumes

Docker Compose creates persistent volumes:
- `postgres_data` - Database data (persists between restarts)
- `ml_models` - ML model checkpoints

To reset everything:
```bash
docker-compose down -v
```

## Network

All services are on the `ghostwriter_network` bridge network and can communicate using service names:
- `postgres` - Database
- `backend` - API server
- `frontend` - Web interface

## Next Steps

1. **Access the app**: http://localhost:3000
2. **Create/Login**: Use demo credentials or register new account
3. **Upload samples**: Go to Profile section
4. **Generate fingerprint**: After uploading samples
5. **Analyze text**: Use the main text input
6. **Try rewriting**: Requires API keys or Ollama

## Production Deployment

For production, use `docker-compose.prod.yml`:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Make sure to:
- Set strong `SECRET_KEY`
- Use secure database passwords
- Configure proper CORS origins
- Set up SSL/HTTPS
- Use environment variables for secrets
