# Ghostwriter Forensic Analytics

A full-stack forensic analytics application that uses stylometric fingerprinting to detect and attribute AI vs human writing, with a web interface featuring heat map visualization and DSPy-powered style rewriting.

## Features

- **Stylometric Fingerprinting**: Extract features like burstiness, perplexity, and rare-word usage to create unique vector signatures
- **AI Detection**: Use contrastive learning models to determine if text samples were written by the same entity
- **Heat Map Visualization**: Interactive web interface showing which parts of documents "feel" like AI vs human writing
- **Personal Fingerprinting**: Upload past writing to fine-tune your personal fingerprint
- **Style Rewriting**: Use DSPy-optimized LLMs to rewrite AI-generated drafts to match your human voice

## Tech Stack

- **Backend**: FastAPI, PostgreSQL, SQLAlchemy
- **Frontend**: React, TypeScript, Vite
- **ML**: PyTorch, Transformers, DSPy
- **APIs**: OpenAI, Anthropic

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edit .env with your configuration
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Database Setup

```bash
# Using Docker Compose
docker-compose up -d postgres

# Or manually create database
createdb ghostwriter
```

### Running the Application

```bash
# Backend (from backend directory)
uvicorn app.main:app --reload

# Frontend (from frontend directory)
npm run dev
```

## Project Structure

- `backend/` - FastAPI backend with ML models
- `frontend/` - React frontend application
- `ml_models/` - Training scripts and model checkpoints

## License

MIT
