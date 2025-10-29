# GitHub Setup Instructions

Your Streamlit app is ready to push to GitHub! Follow these steps:

## Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in
2. Click the **+** icon (top right) → **New repository**
3. Repository name: `excel-assessment-streamlit` (or your preferred name)
4. Description: "Excel Assessment Pro - Streamlit Application"
5. Set visibility: **Public** (for Streamlit Cloud free tier) or **Private**
6. **Do NOT** initialize with README, .gitignore, or license (we already have these)
7. Click **Create repository**

## Step 2: Push to GitHub

Run these commands in your terminal:

```bash
cd /Users/raghavendra_pratap/Developer/rpwp-dev/excel-assessment-streamlit

# Add remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/excel-assessment-streamlit.git

# Push to GitHub
git branch -M main
git push -u origin main
```

If you're using SSH instead:
```bash
git remote add origin git@github.com:YOUR_USERNAME/excel-assessment-streamlit.git
git branch -M main
git push -u origin main
```

## Step 3: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **New app**
4. Configure:
   - **Repository**: Select `excel-assessment-streamlit`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: Choose your app name (e.g., `excel-assessment-pro`)
5. Click **Deploy**

Your app will be live at: `https://your-app-name.streamlit.app`

## Step 4: Configure App Settings

After deployment:

1. In Streamlit Cloud, go to your app settings
2. The app will automatically use SQLite (ephemeral - resets on restart)
3. For production, consider:
   - Using external database (PostgreSQL)
   - Setting up Google Service Account credentials
   - Configuring environment variables

## Verification Checklist

- [ ] Repository created on GitHub
- [ ] Code pushed successfully
- [ ] Streamlit Cloud app deployed
- [ ] App accessible via URL
- [ ] Default admin login works
- [ ] Google Sheets API configured in Settings

## Quick Test Commands

Test locally before deploying:
```bash
cd excel-assessment-streamlit
pip install -r requirements.txt
python setup.py
streamlit run app.py
```

## Troubleshooting

### Authentication Issues
- Make sure you're signed in to GitHub
- Check you have push permissions to the repository

### Push Errors
- Verify remote URL: `git remote -v`
- Check branch name: `git branch`

### Streamlit Cloud Issues
- Check that `app.py` is in the root directory
- Verify all dependencies in `requirements.txt`
- Check logs in Streamlit Cloud dashboard

## Next Steps After Deployment

1. Change default admin password (Settings → Change Password)
2. Configure Google Sheets API credentials
3. Create your first assessment
4. Test the candidate invitation flow
5. Customize branding if needed

