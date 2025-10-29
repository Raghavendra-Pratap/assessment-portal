# Security Guidelines

## 🔒 Security Best Practices

This document outlines security measures for the Excel Assessment Pro Streamlit application.

## ⚠️ Never Commit These Files

The following files are automatically excluded via `.gitignore`:

- ✅ **Database files** (`*.db`, `*.sqlite`, `data/`)
- ✅ **Credentials** (`*.json`, `credentials/`, `*.key`, `*.pem`)
- ✅ **Environment variables** (`.env`, `.env.local`)
- ✅ **Streamlit secrets** (`.streamlit/secrets.toml`)
- ✅ **API keys and secrets** (`*_secret*`, `api_keys.txt`)

## 🔑 Default Credentials

**IMPORTANT:** The default admin credentials are for initial setup only:

- **Email:** `admin@example.com`
- **Password:** `admin123`

**⚠️ CRITICAL:** Change these credentials immediately after first deployment!

## 🔐 Storing Sensitive Data

### For Local Development

1. **Never commit** `.env` files or credential JSON files
2. Use environment variables:
   ```bash
   export GOOGLE_CREDENTIALS='{"type":"service_account",...}'
   ```

### For Streamlit Cloud

1. Use **Streamlit Secrets** (recommended):
   - Go to your app settings
   - Click "Secrets"
   - Add secrets as key-value pairs
   - Access via `st.secrets["google_credentials"]`

2. Example secrets structure:
   ```toml
   [google]
   service_account = """
   {
     "type": "service_account",
     "project_id": "...",
     ...
   }
   """
   ```

### For Production

1. Use environment variables or secrets management:
   - Streamlit Cloud Secrets
   - AWS Secrets Manager
   - Google Secret Manager
   - Azure Key Vault

## 🛡️ Security Checklist

### Before Deployment

- [ ] Changed default admin password
- [ ] Removed any hardcoded credentials from code
- [ ] Verified `.gitignore` includes all sensitive files
- [ ] Google Service Account JSON stored securely
- [ ] Database not exposed publicly
- [ ] HTTPS enabled (Streamlit Cloud default)

### Regular Maintenance

- [ ] Rotate passwords periodically
- [ ] Review access logs
- [ ] Update dependencies for security patches
- [ ] Monitor for exposed secrets in git history
- [ ] Use strong passwords (min 12 characters)

## 📋 Google Service Account Security

### Best Practices

1. **Limited Permissions:**
   - Only grant necessary permissions to service account
   - Use IAM roles with minimum required access

2. **Key Management:**
   - Store keys securely (never in git)
   - Rotate keys regularly
   - Use different keys for dev/prod

3. **Access Control:**
   - Restrict service account to specific sheets/folders
   - Use domain-wide delegation only if necessary

## 🚨 If Credentials Are Exposed

If you accidentally commit sensitive data:

1. **Immediate Actions:**
   ```bash
   # Remove from git history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch path/to/sensitive/file" \
     --prune-empty --tag-name-filter cat -- --all
   
   git push origin --force --all
   ```

2. **Rotate Credentials:**
   - Change all passwords
   - Regenerate API keys
   - Revoke and recreate service account keys

3. **Review Access:**
   - Check who has access to the repository
   - Review git history
   - Enable repository security alerts

## 📝 Code Security

### Password Handling

- ✅ Passwords are hashed using SHA-256 (consider upgrading to bcrypt/argon2)
- ✅ Never log passwords in plain text
- ✅ Use secure password reset flows

### Token Security

- ✅ Assessment tokens are UUID-based (cryptographically random)
- ✅ Tokens have expiration dates
- ✅ Single-use tokens where applicable

### Database Security

- ✅ SQL injection protection via SQLAlchemy ORM
- ✅ Database files excluded from git
- ✅ Sensitive data encrypted at rest (when using cloud databases)

## 🔍 Security Audit

### Check for Sensitive Data

Before each commit, verify:

```bash
# Check for potential secrets
git diff --cached | grep -i "password\|secret\|key\|token" | grep -v "^#" | grep -v "admin123"

# Verify no credentials in tracked files
git ls-files | xargs grep -i "service_account\|private_key" || echo "No credentials found"
```

## 📚 Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Streamlit Security Best Practices](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/security)
- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)

## 🆘 Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** create a public issue
2. Contact repository maintainers privately
3. Provide detailed information about the vulnerability
4. Allow time for fix before public disclosure

## ✅ Current Security Status

- ✅ No credentials in repository
- ✅ Database files excluded
- ✅ Sensitive files in .gitignore
- ✅ Passwords hashed (SHA-256)
- ⚠️ Consider upgrading to bcrypt for production
- ⚠️ Default password documented (change immediately)
- ✅ Token-based access implemented
- ✅ SQL injection protection (SQLAlchemy ORM)

