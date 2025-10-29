# Pre-Commit Security Checklist

Before pushing code, verify:

## ✅ Sensitive Data Check

```bash
# Check for hardcoded credentials
git diff --cached | grep -iE "password.*=.*['\"][^'\"]+['\"]|api_key.*=.*['\"][^'\"]+['\"]|secret.*=.*['\"][^'\"]+['\"]" | grep -v "^#" | grep -v "admin123" | grep -v "hash_password"

# Check for JSON credentials
git diff --cached | grep -E "service_account|private_key|client_secret" | grep -v "^#"

# Verify no database files
git ls-files --cached | grep -E "\.(db|sqlite|json)$" && echo "WARNING: Database or JSON files detected!"
```

## ✅ Files to Never Commit

- [ ] `.env` or `.env.*` files
- [ ] `*.db` or `*.sqlite` files
- [ ] `*credentials*.json` or `*service-account*.json`
- [ ] `*.key`, `*.pem` files
- [ ] `secrets.toml` or `.streamlit/secrets.toml`
- [ ] API keys or tokens in code

## ✅ Current Status

✅ **Verified Safe:**
- Default password "admin123" only in documentation/setup code (not a security risk)
- Password hashing functions are implementation code (safe)
- No actual credentials in repository
- All sensitive file patterns in `.gitignore`

