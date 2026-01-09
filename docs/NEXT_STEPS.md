# Next Steps to Get Ghostwriter Running

## 1. Environment Configuration

Create a `.env` file in the `backend/` directory:

**Note:** Style rewriting uses Ollama local LLM. See `docs/OLLAMA_SETUP.md` for setup instructions.

```bash
cd backend
cat > .env << EOF
DATABASE_URL=postgresql://ghostwriter:ghostwriter_password@localhost:5432/ghostwriter
SECRET_KEY=your-secret-key-change-this-in-production-use-a-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ollama Configuration (required for text analysis and rewriting)
# See docs/OLLAMA_SETUP.md for setup instructions
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

ENVIRONMENT=development
EOF
```

## 2. Install Backend Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Download spaCy English model
python -m spacy download en_core_web_sm

# Download NLTK data (will happen automatically on first run, but you can do it now)
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('stopwords'); nltk.download('wordnet')"
```

## 3. Set Up Database

### Option A: Using Docker Compose (Recommended)

```bash
# From project root
docker-compose up -d postgres

# Wait for PostgreSQL to be ready, then run migrations
cd backend
alembic upgrade head
```

### Option B: Manual PostgreSQL Setup

```bash
# Create database
createdb ghostwriter

# Or using psql:
psql -U postgres
CREATE DATABASE ghostwriter;
CREATE USER ghostwriter WITH PASSWORD 'ghostwriter_password';
GRANT ALL PRIVILEGES ON DATABASE ghostwriter TO ghostwriter;
\q

# Run migrations
cd backend
alembic upgrade head
```

## 4. Install Frontend Dependencies

```bash
cd frontend
npm install
```

## 5. Run the Application

### Terminal 1: Backend
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Frontend
```bash
cd frontend
npm run dev
```

The application should now be accessible at:
- Frontend: http://localhost:3000 (or the port Vite assigns)
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 6. Initial Testing

1. **Register a new user** at the login page
2. **Upload writing samples** in the Profile section
3. **Generate your fingerprint** after uploading samples
4. **Test text analysis** by pasting some text
5. **Test style rewriting**:
   - **With Ollama**: Install Ollama and set `DEFAULT_LLM_MODEL=ollama` (see `docs/OLLAMA_SETUP.md`)
   - **With OpenAI/Anthropic**: Set API keys in `.env`

## 7. Train the Contrastive Model (Optional but Recommended)

The contrastive model will work with default weights, but for better accuracy, train it:

```bash
cd ml_models
python train_contrastive.py
```

You'll need to provide training data (human and AI text samples) in the `data/training_samples/` directory.

## 8. Known Issues to Address

### Fix DSPy Integration
The DSPy rewriter may need adjustments based on the actual DSPy API. Check:
- `backend/app/ml/dspy_rewriter.py` - May need to update DSPy syntax based on version

### Model Loading
- The contrastive model will use random weights initially. Train it for production use.
- GPT-2 model for perplexity will download on first use (may take time).

### CORS Configuration
- If frontend runs on a different port, update CORS origins in `backend/app/main.py`

## 9. Production Considerations

Before deploying:
- [ ] Change `SECRET_KEY` to a secure random value
- [ ] Set up proper database credentials
- [ ] Configure environment variables securely
- [ ] Train the contrastive model with real data
- [ ] Set up proper logging
- [ ] Add error monitoring
- [ ] Configure rate limiting
- [ ] Set up SSL/HTTPS

## 10. Troubleshooting

### Database Connection Issues
- Check PostgreSQL is running: `docker ps` or `pg_isready`
- Verify DATABASE_URL in `.env` matches your setup
- Check database exists: `psql -l | grep ghostwriter`

### ML Model Issues
- GPT-2 will download automatically (first run may be slow)
- If spaCy model fails, run: `python -m spacy download en_core_web_sm`
- Contrastive model uses random weights until trained

### Frontend Connection Issues
- Check backend is running on port 8000
- Verify CORS settings in `backend/app/main.py`
- Check browser console for errors
