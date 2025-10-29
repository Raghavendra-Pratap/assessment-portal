# Excel Assessment Pro - Streamlit App

A comprehensive Streamlit application that replicates the functionality of the Excel Assessment Pro WordPress plugin. This app provides a complete assessment system with Google Sheets integration, proctoring capabilities, and hybrid grading.

## Features

### Core Features
- ✅ **Assessment Management** - Create, edit, and manage Excel assessments
- ✅ **Question Types** - Support for formula, data-entry, MCQ, and scenario questions
- ✅ **Google Sheets Integration** - Automatic template copying and response collection
- ✅ **Session Management** - Track candidate sessions with unique tokens
- ✅ **Auto-Grading** - Automatic grading for formula, data-entry, and MCQ questions
- ✅ **Manual Review** - Hybrid grading with manual review interface
- ✅ **Candidate Interface** - Token-based access for candidates
- ✅ **Admin Dashboard** - Comprehensive admin interface for managing assessments

### Advanced Features
- 📊 **Analytics Dashboard** - View assessment statistics and completion rates
- 🔒 **Token-Based Access** - Secure invitation links for candidates
- 📝 **Question Import** - Import questions from Google Sheets (coming soon)
- 🎨 **Custom Branding** - Customize colors and branding for recruiters
- ⚙️ **Settings Management** - Configure Google Sheets API and other settings

## Installation

### Prerequisites
- Python 3.8 or higher
- Google Cloud Project with Sheets API and Drive API enabled
- Google Service Account credentials (JSON file)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd excel-assessment-streamlit
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**
   - The database will be automatically created on first run
   - Default admin credentials:
     - Email: `admin@example.com`
     - Password: `admin123`

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. **Access the app**
   - Open your browser to `http://localhost:8501`
   - Login with default credentials
   - Configure Google Sheets API in Settings

## Google Sheets API Setup

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing

2. **Enable APIs**
   - Enable Google Sheets API
   - Enable Google Drive API

3. **Create Service Account**
   - Go to IAM & Admin > Service Accounts
   - Create a new service account
   - Download JSON key file

4. **Configure in App**
   - Go to Settings in the app
   - Paste the entire JSON content in "Google Service Account JSON"
   - Save and test connection

## Usage

### Creating an Assessment

1. Navigate to **Assessments** from the sidebar
2. Click **Create New Assessment**
3. Fill in:
   - Assessment Title
   - Description (optional)
   - Duration (minutes)
4. Add questions:
   - Click **Add Question**
   - Select question type (formula, data-entry, mcq, scenario)
   - Enter question text
   - Add Google Sheet template URL (for formula/data-entry)
   - Configure answer key in JSON format
   - Set points

### Inviting Candidates

1. Open an assessment
2. Click **Invite** button
3. Enter candidate email and name
4. Copy and share the generated invitation link

### Candidate Experience

1. Candidate receives invitation link
2. Opens link and sees consent form
3. Accepts terms and starts assessment
4. Works on Google Sheets templates
5. Submits assessment
6. Receives auto-graded score

### Grading Responses

1. Go to **Sessions** page
2. View submitted assessments
3. Auto-graded scores appear automatically
4. Review and adjust manual scores if needed
5. Add reviewer notes

## Question Types

### Formula Questions
- **Purpose:** Test Excel formula knowledge
- **Answer Key Format:** `{"B2": "=VLOOKUP(A2,D2:E10,2,FALSE)"}`
- **Grading:** Compares formulas and calculated values

### Data Entry Questions
- **Purpose:** Test data entry accuracy
- **Answer Key Format:** `{"B2": "1000", "C2": "1200"}`
- **Grading:** Compares entered values with tolerance

### MCQ Questions
- **Purpose:** Test conceptual knowledge
- **Answer Key Format:** `{"answer": "A"}`
- **Grading:** Simple answer matching

### Scenario Questions
- **Purpose:** Complex real-world scenarios
- **Grading:** Manual review required

## Database Schema

The app uses SQLite database with the following tables:
- `recruiters` - Recruiter/admin accounts
- `assessments` - Assessment definitions
- `questions` - Question details
- `invitations` - Candidate invitations
- `sessions` - Assessment sessions
- `responses` - Candidate responses
- `monitoring_events` - Proctoring events

## Configuration

### Environment Variables
Create a `.env` file for environment-specific settings:
```
STREAMLIT_SERVER_PORT=8501
DATABASE_PATH=./data/assessments.db
```

### Settings
Access Settings page to configure:
- Google Sheets API credentials
- Branding colors
- User profile
- Password changes

## Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect repository
4. Deploy app
5. Set environment variables in cloud settings

### Other Platforms

The app can be deployed to any platform that supports Streamlit:
- Docker
- AWS/Azure/GCP
- Heroku
- Any Python hosting service

## Development

### Project Structure
```
excel-assessment-streamlit/
├── app.py                 # Main entry point
├── pages/                 # Page components
│   ├── admin_dashboard.py
│   ├── admin_assessments.py
│   ├── admin_sessions.py
│   ├── admin_settings.py
│   └── candidate_assessment.py
├── src/
│   ├── database/         # Database models
│   ├── services/         # Business logic
│   │   ├── google_sheets.py
│   │   └── grading.py
│   └── utils/            # Utilities
│       └── auth.py
├── data/                 # Database files (gitignored)
└── requirements.txt
```

## Troubleshooting

### Google Sheets API Errors
- Verify service account JSON is correct
- Check API is enabled in Google Cloud Console
- Ensure service account has access to sheets

### Database Issues
- Delete `data/assessments.db` to reset database
- Check file permissions

### Import Errors
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check Python version (3.8+)

## Security Notes

- Change default admin password immediately
- Store Google credentials securely
- Use environment variables for sensitive data
- Enable HTTPS in production

## License

GPL v2 or later

## Support

For issues and questions, please open an issue on GitHub.

