# Ghostwriter Forensic Analytics - Setup Script (PowerShell)
# This script automates the setup process for the application on Windows

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Ghostwriter setup..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python 3 is not installed. Please install Python 3.10+ first." -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js is not installed. Please install Node.js 18+ first." -ForegroundColor Red
    exit 1
}

# Check if Docker is installed (optional)
try {
    docker --version | Out-Null
    Write-Host "✓ Docker found" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Docker is not installed. You'll need to set up PostgreSQL manually." -ForegroundColor Yellow
}

# Backend Setup
Write-Host ""
Write-Host "📦 Setting up backend..." -ForegroundColor Cyan
Set-Location backend

# Create virtual environment if it doesn't exist
if (-Not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
& .\venv\Scripts\Activate.ps1

# Install Python dependencies
Write-Host "Installing Python dependencies (this may take a while)..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model
Write-Host "Downloading spaCy English model..."
python -m spacy download en_core_web_sm

# Download NLTK data
Write-Host "Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('averaged_perceptron_tagger', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True)"

# Create .env file if it doesn't exist
if (-Not (Test-Path ".env")) {
    if (Test-Path ".env.template") {
        Write-Host "Creating .env file from template..."
        Copy-Item .env.template .env
        Write-Host "⚠️  Please edit backend/.env and add your API keys and database credentials" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  .env.template not found. Please create backend/.env manually" -ForegroundColor Yellow
    }
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

Set-Location ..

# Frontend Setup
Write-Host ""
Write-Host "📦 Setting up frontend..." -ForegroundColor Cyan
Set-Location frontend

# Install Node dependencies
Write-Host "Installing Node.js dependencies..."
npm install

Set-Location ..

# Database Setup
Write-Host ""
Write-Host "🗄️  Setting up database..." -ForegroundColor Cyan

# Check if Docker is available
try {
    docker --version | Out-Null
    docker-compose --version | Out-Null
    
    Write-Host "Starting PostgreSQL with Docker Compose..."
    docker-compose up -d postgres
    
    Write-Host "Waiting for PostgreSQL to be ready..."
    Start-Sleep -Seconds 5
    
    # Run database migrations
    Write-Host "Running database migrations..."
    Set-Location backend
    & .\venv\Scripts\Activate.ps1
    alembic upgrade head
    
    Set-Location ..
    Write-Host "✓ Database setup complete" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Docker not available. Please set up PostgreSQL manually and run:" -ForegroundColor Yellow
    Write-Host "   cd backend && .\venv\Scripts\Activate.ps1 && alembic upgrade head"
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Edit backend/.env and add your API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY)"
Write-Host "2. Make sure your database is running"
Write-Host "3. Start the backend: cd backend && .\venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload"
Write-Host "4. Start the frontend: cd frontend && npm run dev"
Write-Host ""
Write-Host "For more details, see NEXT_STEPS.md"
