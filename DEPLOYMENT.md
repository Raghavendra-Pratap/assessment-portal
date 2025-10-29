# Deployment Guide

## Streamlit Cloud Deployment

### Step 1: Prepare Repository

1. Ensure all code is committed to Git
2. Push to GitHub repository
3. Make sure `.gitignore` properly excludes sensitive files

### Step 2: Create Streamlit Cloud App

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select repository and branch
5. Set main file path to `app.py`
6. Click "Deploy"

### Step 3: Configure Environment

The app will work out of the box, but you may want to:

1. Set environment variables in Streamlit Cloud settings
2. Configure database persistence (Streamlit Cloud has ephemeral storage)
3. Set up Google Service Account credentials in Settings page

## Alternative Deployment Options

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t excel-assessment-app .
docker run -p 8501:8501 excel-assessment-app
```

### Railway Deployment

1. Connect GitHub repository to Railway
2. Railway will auto-detect Python app
3. Set start command: `streamlit run app.py`
4. Deploy

### Heroku Deployment

Create `Procfile`:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

Deploy:
```bash
heroku create your-app-name
git push heroku main
```

## Database Considerations

**Important:** Streamlit Cloud has ephemeral storage. Database will reset on each deployment restart.

Solutions:
1. Use external database (PostgreSQL, MySQL) for production
2. Use cloud storage for database file persistence
3. Export/import data regularly

## Environment Variables

For production, set these environment variables:

- `STREAMLIT_SERVER_PORT` - Server port
- `DATABASE_URL` - External database URL (if using)
- `GOOGLE_CREDENTIALS` - Google Service Account JSON (encoded)

## Security Checklist

- [ ] Change default admin password
- [ ] Use environment variables for sensitive data
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Use secure database connections
- [ ] Set up proper authentication
- [ ] Regular security updates

