#!/bin/bash

# Ghostwriter Forensic Analytics - Setup Script
# This script automates the setup process for the application

set -e  # Exit on error

echo "🚀 Starting Ghostwriter setup..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.10+ first.${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js 18+ first.${NC}"
    exit 1
fi

# Check if Docker is installed (optional, for database)
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker is not installed. You'll need to set up PostgreSQL manually.${NC}"
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"

# Backend Setup
echo ""
echo "📦 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies (this may take a while)..."
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model
echo "Downloading spaCy English model..."
python -m spacy download en_core_web_sm || echo "Warning: Could not download spaCy model. You may need to install it manually."

# Download NLTK data
echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('averaged_perceptron_tagger', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True)" || echo "Warning: Could not download NLTK data."

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        echo "Creating .env file from template..."
        cp .env.template .env
        echo -e "${YELLOW}⚠️  Please edit backend/.env and add your API keys and database credentials${NC}"
    else
        echo -e "${YELLOW}⚠️  .env.template not found. Please create backend/.env manually${NC}"
    fi
else
    echo "✓ .env file already exists"
fi

cd ..

# Frontend Setup
echo ""
echo "📦 Setting up frontend..."
cd frontend

# Install Node dependencies
echo "Installing Node.js dependencies..."
npm install

cd ..

# Database Setup
echo ""
echo "🗄️  Setting up database..."

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "Starting PostgreSQL with Docker Compose..."
    docker-compose up -d postgres
    
    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
    
    # Run database migrations
    echo "Running database migrations..."
    cd backend
    source venv/bin/activate
    alembic upgrade head || echo "Warning: Could not run migrations. Make sure PostgreSQL is running."
    cd ..
    
    echo -e "${GREEN}✓ Database setup complete${NC}"
else
    echo -e "${YELLOW}⚠️  Docker not available. Please set up PostgreSQL manually and run:${NC}"
    echo "   cd backend && source venv/bin/activate && alembic upgrade head"
fi

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env and add your API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY)"
echo "2. Make sure your database is running"
echo "3. Start the backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "4. Start the frontend: cd frontend && npm run dev"
echo ""
echo "For more details, see docs/NEXT_STEPS.md"
