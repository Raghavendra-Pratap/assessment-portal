# Quick Start Guide

Get up and running with Excel Assessment Pro in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Initialize Database

```bash
python setup.py
```

This will:
- Create the SQLite database
- Create default admin user (admin@example.com / admin123)

## Step 3: Run the App

```bash
streamlit run app.py
```

## Step 4: Login

- Go to `http://localhost:8501`
- Login with:
  - Email: `admin@example.com`
  - Password: `admin123`

## Step 5: Configure Google Sheets

1. Go to **Settings** in the sidebar
2. Get Google Service Account JSON from Google Cloud Console
3. Paste the JSON in "Google Service Account JSON" field
4. Click "Save Google Sheets Config"
5. Test the connection

## Step 6: Create Your First Assessment

1. Go to **Assessments**
2. Click **Create New Assessment**
3. Fill in:
   - Title: "Excel Skills Test"
   - Duration: 60 minutes
4. Click **Create Assessment**
5. Add questions:
   - Click **Add Question**
   - Select type: "formula"
   - Enter question text
   - Add Google Sheet template URL
   - Add answer key JSON

## Step 7: Invite Candidates

1. Open your assessment
2. Click **Invite** button
3. Enter candidate email and name
4. Copy the invitation link
5. Share with candidate

## That's It! 🎉

Your assessment system is ready. Candidates can now:
- Open the invitation link
- Take the assessment
- Submit for auto-grading
- View results

## Next Steps

- Customize branding in Settings
- Create more assessments
- View sessions and grade responses
- Set up email notifications (coming soon)

