# Troubleshooting Guide

## Common Error: "An error occurred"

If you're seeing a generic "An error occurred" message, here's how to diagnose and fix it:

### 1. Check Backend is Running

**Symptoms:**
- "Cannot connect to server" error
- Network errors in browser console

**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not running, start it:
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### 2. Check Database Connection

**Symptoms:**
- Database-related errors in backend logs
- "OperationalError" in terminal

**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres
# OR
pg_isready

# Start PostgreSQL if using Docker:
docker-compose up -d postgres

# Verify connection:
psql -h localhost -U ghostwriter -d ghostwriter
# Password: ghostwriter_password
```

### 3. Check CORS Configuration

**Symptoms:**
- CORS errors in browser console
- "Access-Control-Allow-Origin" errors

**Solution:**
- Verify frontend is running on port 3000 or 5173
- Check `backend/app/main.py` has correct CORS origins
- Make sure backend allows your frontend URL

### 4. Check Environment Variables

**Symptoms:**
- Authentication errors
- API key errors

**Solution:**
```bash
# Check .env file exists
ls backend/.env

# Verify key variables are set:
cat backend/.env | grep -E "DATABASE_URL|SECRET_KEY"
```

### 5. Check Browser Console

**How to Debug:**
1. Open browser Developer Tools (F12)
2. Go to Console tab
3. Look for error messages
4. Go to Network tab to see failed requests

**Common Issues:**
- `ERR_CONNECTION_REFUSED` - Backend not running
- `CORS error` - CORS misconfiguration
- `401 Unauthorized` - Authentication issue
- `500 Internal Server Error` - Backend error (check backend logs)

### 6. Check Backend Logs

**View Backend Logs:**
```bash
# In the terminal where uvicorn is running
# Look for error messages, stack traces, etc.
```

**Common Backend Errors:**
- Database connection failures
- Missing environment variables
- Import errors
- Model loading errors

### 7. Verify API Endpoints

**Test Backend Directly:**
```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs

# Test registration (should work even without DB for some endpoints)
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### 8. Frontend-Backend Connection

**Verify Connection:**
1. Check frontend is using correct API URL
2. Default: `http://localhost:8000`
3. Can be overridden with `VITE_API_BASE_URL` environment variable

**Test:**
```bash
# From frontend directory
echo $VITE_API_BASE_URL
# Should be empty or set to http://localhost:8000
```

## Quick Diagnostic Checklist

- [ ] Backend is running on port 8000
- [ ] Frontend is running (port 3000 or 5173)
- [ ] Database is running and accessible
- [ ] `.env` file exists with correct values
- [ ] No CORS errors in browser console
- [ ] Network requests show in browser DevTools
- [ ] Backend logs show no errors
- [ ] API health endpoint responds: `curl http://localhost:8000/health`

## Getting More Detailed Errors

The frontend now shows more detailed error messages. Check:
1. **Browser Console** (F12 → Console) - Shows full error details
2. **Network Tab** (F12 → Network) - Shows API request/response details
3. **Backend Terminal** - Shows server-side errors

## Still Having Issues?

1. **Check all services are running:**
   ```bash
   # Terminal 1: Backend
   cd backend && source venv/bin/activate && uvicorn app.main:app --reload
   
   # Terminal 2: Frontend  
   cd frontend && npm run dev
   
   # Terminal 3: Database (if using Docker)
   docker-compose up -d postgres
   ```

2. **Verify ports are not in use:**
   ```bash
   lsof -i :8000  # Backend
   lsof -i :3000  # Frontend
   lsof -i :5432  # PostgreSQL
   ```

3. **Check firewall/security settings** that might block connections

4. **Try accessing API directly:**
   - http://localhost:8000/docs - Should show Swagger UI
   - http://localhost:8000/health - Should return JSON
