# 🛡️ Threat Intelligence Summarizer - Running Status

## ✅ Current Status

### Backend API - RUNNING ✓
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
- **Database**: SQLite (threatintel.db) - Migrated ✓

### Frontend - Installing Dependencies
- **Target URL**: http://localhost:3000
- **Status**: Check the command window that opened
- **Wait for**: "Local: http://localhost:3000" message

---

## 🚀 Quick Start Guide

### 1. Access the Application

Once frontend shows "Local: http://localhost:3000":
1. Open browser to: **http://localhost:3000**
2. You'll see the login page

### 2. Create Your Account

1. Click "Need an account? Register"
2. Enter email: `admin@example.com`
3. Enter password: `password123`
4. Click "Register"

### 3. Login

1. Use the same credentials to login
2. You'll be redirected to the Dashboard

### 4. Explore Features

**Dashboard** - View today's threat intelligence brief
- Executive summary
- Top 5 CVEs with CVSS scores
- Threat themes
- Defensive recommendations

**Archive** - Browse past daily briefs

**Raw Feed** - View all scraped intelligence items
- Filter by severity (Critical/High/Medium/Low)
- Filter by source (NVD, CISA, Krebs, etc.)
- Trigger manual scrape

**Settings** - Configure your account
- Toggle email digest
- Set delivery time
- Logout

---

## 🧪 Test the Scrapers

### Option 1: Via API (Backend Only)

Open http://localhost:8000/docs and try:

1. **Register a user** - POST /auth/register
   ```json
   {
     "email": "test@example.com",
     "password": "test123"
   }
   ```

2. **Login** - POST /auth/login
   ```json
   {
     "email": "test@example.com",
     "password": "test123"
   }
   ```
   Copy the `access_token` from response

3. **Click "Authorize"** button (top right)
   - Paste token in format: `Bearer YOUR_TOKEN_HERE`

4. **Trigger Scrape** - POST /intel/scrape
   - This will scrape all 7 sources!

5. **View Items** - GET /intel/items
   - See scraped intelligence

### Option 2: Via Frontend (Once Running)

1. Login to http://localhost:3000
2. Go to "Raw Feed" page
3. Click "🔄 Trigger Scrape" button
4. Wait ~10-30 seconds
5. Refresh to see scraped items

---

## 📊 What Gets Scraped

1. **NVD CVE Feed** - Latest 20 CVEs with CVSS scores
2. **CISA KEV** - Known Exploited Vulnerabilities (Critical)
3. **Krebs on Security** - Latest 10 blog posts
4. **The Hacker News** - Latest 10 articles
5. **Bleeping Computer** - Latest 10 articles
6. **Schneier on Security** - Latest 10 posts
7. **US-CERT Alerts** - Latest 10 alerts

---

## 🔧 Troubleshooting

### Frontend Not Starting?
Check the command window for errors. Common issues:
- Node modules installing (wait 1-2 minutes)
- Port 3000 already in use (change in vite.config.js)

### Backend Issues?
- Check: http://localhost:8000/health
- Should return: `{"status":"healthy",...}`

### Can't Login?
- Make sure you registered first
- Check backend logs in the command window

### No Data in Dashboard?
- Trigger a manual scrape first
- Wait for scraping to complete
- LLM briefs are generated locally when `LLM_PROVIDER=local`

---

## ⚠️ Important Notes

### Provider Configuration
The application supports free local providers by default. For paid cloud providers:

1. **Amazon Bedrock** - Required for AI-powered brief generation
   - Get AWS credentials
   - Enable Claude Sonnet 4 model access
   - Update `.env` file

2. **AWS SES** - Required for email digests
   - Verify sender email
   - Update `.env` file

### Free Local Providers (Current Setup)
You can still:
- ✅ Scrape all 7 intelligence sources
- ✅ View raw intelligence feed
- ✅ Filter and search items
- ✅ User authentication
- ✅ Generate daily briefs with local rule-based analysis
- ✅ Log digest output without sending paid SES email

---

## 📁 Project Files

- **Backend**: `backend/` folder
- **Frontend**: `frontend/` folder
- **Database**: `backend/threatintel.db`
- **Config**: `.env` file
- **Logs**: Check command windows

---

## 🎯 Next Steps

1. **Wait for frontend** to finish installing (check command window)
2. **Open** http://localhost:3000
3. **Register** and **Login**
4. **Trigger a scrape** to populate data
5. **Explore** the dashboard and features!

---

## 🛑 To Stop the Application

1. Close both command windows (backend and frontend)
2. Or press `Ctrl+C` in each window

## 🔄 To Restart

1. Run: `backend/run.py` for backend
2. Run: `frontend/start.bat` for frontend

---

**Enjoy your Threat Intelligence Summarizer!** 🛡️
