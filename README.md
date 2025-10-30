# Secure Admin Page (Develop reset)

This branch starts with a single TOTP-protected admin page.

Setup

1) Install deps
```
pip install -r requirements.txt
```

2) Provision TOTP secret (do one):
- Environment (recommended):
  - Export `ADMIN_TOTP_SECRET` to your deployment
  - Optional: `ADMIN_TOTP_ISSUER`, `ADMIN_TOTP_ACCOUNT`
- Local file (dev only, ignored by git):
  - Create `config/admin_totp.json` with:
    {
      "secret": "BASE32SECRET",
      "issuer": "ExcelAssessment",
      "account": "admin"
    }

Generate a secret:
```
python -c "import pyotp; print(pyotp.random_base32())"
```

3) Add secret to your authenticator app:
- In your app, add an account with the generated secret (manual entry)
- Name: issuer/account

4) Run
```
streamlit run app.py
```
