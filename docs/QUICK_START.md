# Quick Start Guide

## 🚀 Fastest Way to Get Started

### Option 1: Automated Setup (Recommended)

**Linux/Mac:**
```bash
./setup.sh
```

### Option 2: Manual Setup

1. **Backend Setup:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.template .env
# Edit .env with your API keys
```

2. **Frontend Setup:**
```bash
cd frontend
npm install
```

3. **Database Setup:**
```bash
# Using Docker
docker-compose up -d postgres

# Run migrations
cd backend
source venv/bin/activate
alembic upgrade head
```

4. **Start Services:**
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## 📝 Required Configuration

### 1. Create `.env` file in `backend/` directory:

```bash
cd backend
cp .env.template .env
```

### 2. Edit `.env` and add:

- **Database URL** (if not using Docker defaults)
- **SECRET_KEY** (generate a random string)
- **LLM Provider** (choose one):
  - **Ollama** (free, local): Set `DEFAULT_LLM_MODEL=ollama` and `OLLAMA_MODEL=llama2`
  - **OpenAI**: Set `OPENAI_API_KEY=your-key`
  - **Anthropic**: Set `ANTHROPIC_API_KEY=your-key`

### 3. Generate a Secret Key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## ✅ Verify Installation

1. **Check Backend:**
   - Visit: http://localhost:8000/docs
   - Should see FastAPI Swagger UI

2. **Check Frontend:**
   - Visit: http://localhost:3000 (or port shown by Vite)
   - Should see login page

3. **Test Database:**
   ```bash
   # From backend directory
   python -c "from app.models.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
   ```

## 🐛 Common Issues

### Database Connection Error
- Check PostgreSQL is running: `docker ps` or `pg_isready`
- Verify DATABASE_URL in `.env` matches your setup
- Try: `docker-compose restart postgres`

### Module Not Found Errors
- Make sure virtual environment is activated
- Reinstall: `pip install -r requirements.txt`

### DSPy Import Errors
- DSPy is optional - the app will use direct API calls as fallback
- To use DSPy: `pip install dspy-ai`

### Frontend Can't Connect to Backend
- Check backend is running on port 8000
- Verify CORS settings in `backend/app/main.py`
- Check browser console for errors

## 🎯 First Steps After Setup

### Option 1: Use Default Demo User (Quick Start)

```bash
# Create default demo user
cd backend
source venv/bin/activate
python scripts/seed_default_user.py
```

Then log in with:
- **Email:** `demo@ghostwriter.com`
- **Password:** `demo123`

### Option 2: Register Your Own Account

1. **Register a new user** at the login page
2. **Upload writing samples** in Profile section (at least 2-3 samples)
3. **Generate your fingerprint** after uploading samples
4. **Test text analysis** by pasting some text
5. **Try style rewriting** (requires API keys or Ollama)

## 📚 Next Steps

- See `docs/NEXT_STEPS.md` for detailed setup instructions
- See `docs/OLLAMA_SETUP.md` for local LLM setup (free alternative)
- See `README.md` for project overview
- Check API documentation at http://localhost:8000/docs
