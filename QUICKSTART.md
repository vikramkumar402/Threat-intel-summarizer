# Quick Start Guide - Local Development (Without Docker)

Since Docker is not available, here's how to run the application locally:

## Prerequisites

1. **PostgreSQL Database**
   - Install PostgreSQL from: https://www.postgresql.org/download/windows/
   - Create a database named `threatintel`
   - Note your username and password

2. **Python 3.11+** ✅ (Already installed - Python 3.14.3)

3. **Node.js 18+**
   - Install from: https://nodejs.org/

4. **AWS Credentials**
   - AWS Access Key with Bedrock and SES permissions
   - Bedrock model access enabled
   - SES email verified

## Setup Steps

### 1. Configure Environment

Create a `.env` file in the project root:

```env
DATABASE_URL=sqlite:///./threatintel.db
LLM_PROVIDER=local
EMAIL_PROVIDER=log
JWT_SECRET=your_random_secret_key_generate_with_openssl
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=30
JWT_REFRESH_EXPIRE_DAYS=7
APP_BASE_URL=http://localhost:3000
```

This is the zero-cost mode. The app still scrapes and generates briefs using local rule-based analysis.

If you want cloud LLM summaries without Bedrock, switch to Groq:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
EMAIL_PROVIDER=log
```

### 2. Install Backend Dependencies

```bash
cd backend
pip install fastapi uvicorn sqlalchemy alembic httpx beautifulsoup4 feedparser boto3 python-dotenv python-jose passlib python-multipart apscheduler slowapi structlog pytest pytest-asyncio pydantic-settings jinja2 psycopg2-binary
```

Note: If psycopg2-binary fails, install PostgreSQL first, then retry.

### 3. Run Database Migrations

```bash
cd backend
alembic upgrade head
```

### 4. Start Backend Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### 5. Install Frontend Dependencies

Open a new terminal:

```bash
cd frontend
npm install
```

### 6. Start Frontend Development Server

```bash
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:3000

## Access the Application

1. Open browser to: http://localhost:3000
2. Register a new account
3. Login and explore the dashboard

## Manual Testing (Without Full Setup)

If you want to test individual components:

### Test Scrapers
```bash
cd backend
python -c "
import asyncio
from app.scrapers.nvd import NVDScraper

async def test():
    scraper = NVDScraper()
    items = await scraper.scrape()
    print(f'Scraped {len(items)} items')
    for item in items[:3]:
        print(f'- {item.title}')
    await scraper.close()

asyncio.run(test())
"
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:8000/health

# API documentation
# Open: http://localhost:8000/docs
```

## Alternative: Use SQLite (No PostgreSQL Required)

If you don't want to install PostgreSQL, modify the `.env` file:

```env
DATABASE_URL=sqlite:///./threatintel.db
```

Then update `backend/alembic/versions/001_initial_migration.py` to remove PostgreSQL-specific JSON type:
- Change `postgresql.JSON` to `sa.JSON`

## Troubleshooting

**psycopg2-binary installation fails:**
- Install PostgreSQL first: https://www.postgresql.org/download/windows/
- Or use SQLite as shown above

**Port already in use:**
- Change backend port: `uvicorn app.main:app --port 8001`
- Change frontend port in `vite.config.js`

**AWS Bedrock errors:**
- Ensure you have requested model access in AWS Console
- Verify IAM permissions
- Check AWS credentials are correct

**Database connection errors:**
- Verify PostgreSQL is running
- Check DATABASE_URL in .env
- Ensure database `threatintel` exists

## Next Steps

Once running:
1. Register an account at http://localhost:3000/login
2. Go to Settings to configure email digest
3. Trigger a manual scrape from the Intel page
4. View the generated brief on the Dashboard

The automated daily pipeline will run at 06:00 UTC when the backend is running.
