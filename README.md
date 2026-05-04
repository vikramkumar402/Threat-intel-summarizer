# Threat Intelligence Summarizer

A production-grade automated threat intelligence platform that scrapes open-source security news and CVE feeds, processes them through Amazon Bedrock (Claude), and generates structured daily briefings served via a dashboard and email digest.

## Features

- **Automated Daily Scraping**: Collects intelligence from 7+ sources (NVD, CISA KEV, Krebs, The Hacker News, Bleeping Computer, Schneier, US-CERT)
- **LLM-Powered Analysis**: Uses Amazon Bedrock (Claude Sonnet 4) to generate executive summaries, identify top CVEs, extract threat themes, and provide defensive recommendations
- **Modern Dashboard**: React + Tailwind CSS dark-themed interface with severity badges, sortable tables, and markdown export
- **Email Digests**: Automated daily email delivery via AWS SES with customizable delivery times
- **JWT Authentication**: Secure user authentication with bcrypt password hashing
- **RESTful API**: FastAPI backend with rate limiting, CORS, and structured logging
- **Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Containerized**: Docker + docker-compose for easy deployment

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy + Alembic
- PostgreSQL
- Amazon Bedrock (Claude)
- AWS SES
- APScheduler
- httpx + BeautifulSoup4 + feedparser

### Frontend
- React 18
- Tailwind CSS (dark mode)
- Vite
- Axios
- React Router

## Project Structure

```
threat-intel-summarizer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration management
│   │   ├── database.py          # Database connection
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API endpoints
│   │   │   ├── auth.py          # Authentication
│   │   │   ├── intel.py         # Intelligence items
│   │   │   ├── briefs.py        # Daily briefs
│   │   │   └── users.py         # User settings
│   │   ├── scrapers/            # Data scrapers
│   │   │   ├── base.py          # Abstract base class
│   │   │   ├── nvd.py           # NVD CVE scraper
│   │   │   ├── cisa.py          # CISA KEV scraper
│   │   │   ├── rss.py           # RSS feed scrapers
│   │   │   └── uscert.py        # US-CERT scraper
│   │   ├── services/
│   │   │   ├── llm_service.py   # Bedrock integration
│   │   │   ├── scheduler.py     # APScheduler jobs
│   │   │   └── email_service.py # SES email service
│   │   ├── prompts/
│   │   │   └── daily_brief.txt  # LLM prompt template
│   │   └── templates/
│   │       └── digest_email.html # Email template
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # Pytest tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/               # React pages
│   │   ├── components/          # Reusable components
│   │   ├── api/                 # API client
│   │   └── main.jsx             # Entry point
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── .env.example
```

## Setup Instructions

### Prerequisites

- Docker & Docker Compose
- AWS Account with:
  - Bedrock access (Claude Sonnet 4 model enabled)
  - SES configured and verified
  - IAM credentials with appropriate permissions

### Local Development Setup

1. **Clone the repository**
   ```bash
   cd threat-intel-summarizer
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and fill in your AWS credentials:
   ```env
   DATABASE_URL=postgresql://threatintel:changeme@db:5432/threatintel
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-east-1
   BEDROCK_MODEL_ID=claude-sonnet-4-20250514
   SES_FROM_EMAIL=briefs@yourdomain.com
   JWT_SECRET=your_random_secret_key_here
   JWT_ALGORITHM=HS256
   JWT_EXPIRE_MINUTES=1440
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Free Mode (No AWS Cost)

The backend supports a free mode that avoids Bedrock and SES calls.

Set these in `.env`:

```env
DATABASE_URL=sqlite:///./threatintel.db
LLM_PROVIDER=local
EMAIL_PROVIDER=log
JWT_SECRET=replace-with-a-long-random-secret
APP_BASE_URL=http://localhost:3000
```

Or use Groq as a cloud LLM without Bedrock:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
EMAIL_PROVIDER=log
```

In free mode:
- Scrapers, ingestion, search, dashboards, and auth all work.
- Daily briefs are generated by local rule-based logic (no Bedrock billing).
- Email delivery is skipped (no SES billing).

### Start locally in free mode

Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Manual Setup (Without Docker)

#### Backend

1. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL**
   ```bash
   createdb threatintel
   ```

3. **Run migrations**
   ```bash
   alembic upgrade head
   ```

4. **Start the backend**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend

1. **Install Node dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**
   ```bash
   npm run dev
   ```

## Usage

### First Time Setup

1. Navigate to http://localhost/login
2. Register a new account
3. Login with your credentials
4. Go to Settings to configure email digest preferences

### Manual Scraping

Trigger a manual scrape from the Raw Feed page or via API:
```bash
curl -X POST http://localhost:8000/intel/scrape \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Automated Daily Pipeline

The scheduler runs automatically at 06:00 UTC daily and:
1. Scrapes all configured sources
2. Deduplicates by URL
3. Processes intelligence through the configured LLM provider
4. Generates and stores daily brief
5. Sends email digests to subscribed users

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Intelligence Items
- `GET /intel/items` - List intelligence items (paginated, filterable)
- `GET /intel/items/{id}` - Get specific item
- `POST /intel/scrape` - Trigger manual scrape

### Daily Briefs
- `GET /briefs/latest` - Get today's brief
- `GET /briefs/{date}` - Get brief for specific date
- `GET /briefs/` - List all briefs (paginated)

### User Settings
- `PUT /users/me/digest-settings` - Update email digest settings
- `GET /users/me/digest-preview` - Preview email digest

### Health
- `GET /health` - Health check endpoint

## AWS Deployment

### Required IAM Permissions

Create an IAM user/role with the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    }
  ]
}
```

### SES Configuration

1. Verify your sender email address in AWS SES
2. If in sandbox mode, verify recipient email addresses
3. Request production access for unrestricted sending

### Bedrock Setup

1. Navigate to AWS Bedrock console
2. Request access to Claude Sonnet 4 model
3. Wait for approval (usually instant for most regions)

### Deployment Options

#### Free-tier deployment (recommended)

- Backend: Render free Web Service
- Database: Neon free Postgres (or SQLite for small/single-instance usage)
- Frontend: Netlify or Vercel free static hosting

Frontend production API endpoint can be configured with:

```env
VITE_API_BASE_URL=https://your-backend.example.com
```

Backend CORS should include your frontend URL via:

```env
APP_BASE_URL=https://your-frontend.example.com
```

Note: Fully non-demo AI + email mode is not free because Bedrock/SES are paid services.

#### Option 1: EC2 with Docker

1. Launch an EC2 instance (t3.medium or larger recommended)
2. Install Docker and Docker Compose
3. Clone repository and configure `.env`
4. Run `docker-compose up -d`
5. Configure security groups to allow ports 80 and 443

#### Option 2: ECS Fargate

1. Build and push Docker images to ECR
2. Create ECS task definitions for backend and frontend
3. Set up Application Load Balancer
4. Configure RDS PostgreSQL instance
5. Deploy services to ECS cluster

#### Option 3: AWS App Runner

1. Push backend to ECR
2. Create App Runner service
3. Configure environment variables
4. Set up RDS PostgreSQL
5. Deploy frontend to S3 + CloudFront

## Testing

Run backend tests:
```bash
cd backend
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_scrapers.py -v
```

## Adding New Scraper Sources

1. Create a new scraper class in `backend/app/scrapers/`:
   ```python
   from app.scrapers.base import BaseScraper
   from app.schemas import IntelItem
   
   class NewSourceScraper(BaseScraper):
       def __init__(self):
           super().__init__("SourceName")
           self.url = "https://source.com/feed"
       
       async def fetch(self) -> str:
           # Implement fetch logic
           pass
       
       async def parse(self, raw_data: str) -> List[dict]:
           # Implement parse logic
           pass
       
       async def normalize(self, parsed_data: List[dict]) -> List[IntelItem]:
           # Implement normalization logic
           pass
   ```

2. Add to `backend/app/scrapers/__init__.py`

3. Import and add to scheduler in `backend/app/services/scheduler.py`:
   ```python
   from app.scrapers import NewSourceScraper
   
   # In _run_scrapers method:
   scrapers = [
       # ... existing scrapers
       NewSourceScraper(),
   ]
   ```

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running: `docker-compose ps`
- Check connection string in `.env`
- Verify migrations: `docker-compose exec backend alembic current`

### Scraper Failures
- Check logs: `docker-compose logs backend`
- Verify network connectivity to source URLs
- Some sources may have rate limiting

### Bedrock Errors
- Verify IAM permissions
- Ensure model access is granted in Bedrock console
- Check AWS region configuration

### Email Not Sending
- Verify SES email addresses
- Check SES sending limits
- Review CloudWatch logs for SES

## Security Considerations

- Never commit `.env` file with real credentials
- Use strong JWT secrets (generate with `openssl rand -hex 32`)
- Enable HTTPS in production
- Regularly update dependencies
- Implement rate limiting on public endpoints
- Use AWS Secrets Manager for production credentials

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:
- Open a GitHub issue
- Check existing documentation
- Review API docs at `/docs` endpoint
