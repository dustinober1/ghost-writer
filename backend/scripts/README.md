# Backend Scripts

Utility scripts for the Ghostwriter backend.

## Seed Default User

Create a default demo user for development/testing:

```bash
cd backend
source venv/bin/activate
python scripts/seed_default_user.py
```

**Default Credentials:**
- Email: `demo@ghostwriter.com`
- Password: `demo123`

⚠️ **Warning:** This is for development only. Do not use in production!

## Usage

After running the seed script, you can log in to the application at http://localhost:3000 with:
- Email: `demo@ghostwriter.com`
- Password: `demo123`
