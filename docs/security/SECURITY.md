# Security Guide

This document outlines security best practices, secret management, and deployment procedures for the Charting AI Project.

## Table of Contents

1. [Secret Management](#secret-management)
2. [Secret Rotation](#secret-rotation)
3. [Handling Leaked Secrets](#handling-leaked-secrets)
4. [Git History Cleanup](#git-history-cleanup)
5. [Azure SQL Database Hardening](#azure-sql-database-hardening)
6. [Production Deployment Checklist](#production-deployment-checklist)

---

## Secret Management

### Environment Variables

**Never commit secrets to version control.** All sensitive configuration must be provided via environment variables.

### Required Secrets

- `FLASK_SECRET_KEY`: Used for Flask session signing and CSRF protection
- `GEMINI_API_KEY`: Google Gemini API authentication key
- `AZURE_SQL_PASSWORD`: Azure SQL Database password
- `AZURE_SQL_USERNAME`: Azure SQL Database username (sensitive)

### Best Practices

- ✅ Use strong, unique values for all secrets
- ✅ Rotate secrets regularly (see [Secret Rotation](#secret-rotation))
- ✅ Use different secrets for development, staging, and production
- ✅ Never log or print secret values
- ✅ Use secret management services (Azure Key Vault, AWS Secrets Manager, etc.) in production
- ❌ Never hardcode secrets in source code
- ❌ Never commit `.env` files
- ❌ Never share secrets via email, chat, or unencrypted channels

---

## Secret Rotation

### When to Rotate Secrets

Rotate secrets immediately if:
- A secret is suspected to be compromised
- An employee with access leaves the organization
- As part of regular security maintenance (recommended: every 90 days)
- After a security incident

### Rotation Steps

#### 1. Flask Secret Key

**Impact**: All existing user sessions will be invalidated. Users will need to log in again.

```bash
# Generate a new secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update in your environment (Azure App Service, Heroku, etc.)
# For Azure App Service:
az webapp config appsettings set --name <app-name> --resource-group <rg-name> --settings FLASK_SECRET_KEY="<new-key>"

# Restart the application
az webapp restart --name <app-name> --resource-group <rg-name>
```

#### 2. Gemini API Key

1. Generate a new API key in Google Cloud Console
2. Update `GEMINI_API_KEY` environment variable
3. Restart the application
4. Verify the application works with the new key
5. Revoke the old API key after verification

#### 3. Azure SQL Database Password

**Impact**: Brief connection interruption during rotation.

```bash
# 1. Update password in Azure Portal or via Azure CLI
az sql db update --server <server-name> --name <db-name> --admin-password <new-password>

# 2. Update AZURE_SQL_PASSWORD environment variable
az webapp config appsettings set --name <app-name> --resource-group <rg-name> --settings AZURE_SQL_PASSWORD="<new-password>"

# 3. Restart the application
az webapp restart --name <app-name> --resource-group <rg-name>

# 4. Verify database connectivity
# 5. Update password in all other environments (staging, etc.)
```

---

## Handling Leaked Secrets

### Immediate Actions

If a secret is leaked or suspected to be compromised:

1. **Rotate the secret immediately** (see [Secret Rotation](#secret-rotation))
2. **Revoke the compromised secret** if possible (API keys, etc.)
3. **Review access logs** for unauthorized access
4. **Notify your security team** and stakeholders
5. **Document the incident** for post-mortem analysis

### If Secrets Were Committed to Git

If secrets were accidentally committed to the repository:

1. **Rotate all affected secrets immediately** (do not wait for cleanup)
2. **Clean Git history** (see [Git History Cleanup](#git-history-cleanup))
3. **Force push** the cleaned history (coordinate with team)
4. **Notify all team members** to re-clone the repository
5. **Review and update access controls** on the repository

**Important**: Even after cleaning Git history, assume the secrets are compromised if the repository is public or was accessible to unauthorized parties.

---

## Git History Cleanup

If secrets were committed to Git, you must remove them from the entire Git history.

### Prerequisites

Install `git-filter-repo` (recommended) or use `git filter-branch`:

```bash
# Install git-filter-repo (recommended)
pip install git-filter-repo

# Or use git filter-branch (built-in, but slower)
# git filter-branch is already available in Git
```

### Method 1: Using git-filter-repo (Recommended)

```bash
# Backup your repository first!
git clone <repo-url> <repo-backup>

# Remove secrets from entire history
git filter-repo --path app.py --invert-paths  # Remove file entirely (if it contained secrets)
# OR
git filter-repo --replace-text <(echo "old-secret==>new-placeholder")  # Replace specific strings

# Force push (coordinate with team!)
git push origin --force --all
git push origin --force --tags
```

### Method 2: Using git filter-branch

```bash
# Remove a specific file from history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch app.py" \
  --prune-empty --tag-name-filter cat -- --all

# Replace a specific string in history
git filter-branch --force --tree-filter \
  "sed -i 's/old-secret/new-placeholder/g' app.py" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (coordinate with team!)
git push origin --force --all
git push origin --force --tags
```

### After Cleanup

1. **Notify all team members** to:
   - Delete their local repository clones
   - Re-clone the repository
   - Update any local branches

2. **Rotate all affected secrets** (they are still compromised if the repo was public)

3. **Update CI/CD pipelines** if they cached the old history

4. **Consider making the repository private** if it was public

### Warning

- ⚠️ **Force pushing rewrites history** - coordinate with your entire team
- ⚠️ **This is destructive** - ensure you have backups
- ⚠️ **Public repositories**: If secrets were in a public repo, assume they are compromised regardless of cleanup

---

## Azure SQL Database Hardening

### Firewall Rules

Restrict database access to specific IP addresses:

```bash
# Allow specific IP addresses only
az sql server firewall-rule create \
  --resource-group <rg-name> \
  --server <server-name> \
  --name "AllowAppService" \
  --start-ip-address <app-service-outbound-ip> \
  --end-ip-address <app-service-outbound-ip>

# Or allow Azure services only (if app is on Azure)
az sql server firewall-rule create \
  --resource-group <rg-name> \
  --server <server-name> \
  --name "AllowAzureServices" \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### Disable Public Network Access (Recommended)

If your application is hosted on Azure and doesn't need public access:

```bash
# Disable public network access
az sql server update \
  --resource-group <rg-name> \
  --name <server-name> \
  --public-network-access Disabled
```

**Note**: This requires your app to use Private Endpoints or be in the same VNet.

### Connection Encryption

Ensure `AZURE_SQL_ENCRYPT=yes` is set (default). This encrypts data in transit.

### Additional Hardening Checklist

- ✅ Enable Azure SQL Database threat detection
- ✅ Enable auditing and log retention
- ✅ Use Azure AD authentication when possible (future: `DATABASE_AUTH_MODE=aad`)
- ✅ Regularly review and rotate database passwords
- ✅ Limit database user permissions (principle of least privilege)
- ✅ Enable SQL Database vulnerability assessment
- ✅ Configure backup retention policies
- ✅ Enable geo-redundant backups for critical data

---

## Production Deployment Checklist

Before deploying to production, verify all items:

### Environment Configuration

- [ ] `FLASK_ENV=production` is set
- [ ] `FLASK_SECRET_KEY` is set to a strong, unique value (at least 32 characters)
- [ ] `FLASK_DEBUG=0` (debug mode disabled)
- [ ] `GEMINI_API_KEY` is set and valid
- [ ] All `AZURE_SQL_*` variables are set correctly
- [ ] `SESSION_COOKIE_SECURE=True` (automatically set when `FLASK_ENV=production`)
- [ ] `SESSION_COOKIE_HTTPONLY=True` (default)
- [ ] `SESSION_COOKIE_SAMESITE` is set appropriately (default: `Lax`)

### Security Settings

- [ ] HTTPS is enabled and enforced
- [ ] SSL/TLS certificates are valid and not expired
- [ ] Database firewall rules are configured (restrict to app IPs)
- [ ] Database encryption in transit is enabled (`AZURE_SQL_ENCRYPT=yes`)
- [ ] Secrets are stored in a secure vault (Azure Key Vault, etc.)
- [ ] No secrets are logged or exposed in error messages

### Application Settings

- [ ] Application logs do not contain secrets
- [ ] Error pages do not expose stack traces in production
- [ ] Session lifetime is configured appropriately (`PERMANENT_SESSION_DAYS`)
- [ ] Database connection timeout is set (`AZURE_SQL_TIMEOUT`)

### Monitoring & Alerts

- [ ] Application monitoring is configured
- [ ] Database connection monitoring is enabled
- [ ] Alerts are set for failed authentication attempts
- [ ] Log aggregation is configured (Azure Monitor, etc.)

### Testing

- [ ] All routes are tested (`GET /`, `GET /insights`, `POST /chat`)
- [ ] Database connectivity is verified
- [ ] Session cookies are working correctly
- [ ] HTTPS redirect is working (if configured)
- [ ] Error handling does not leak sensitive information

### Documentation

- [ ] Deployment runbook is updated
- [ ] Incident response procedures are documented
- [ ] Team members know how to rotate secrets
- [ ] Security contacts are documented

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [Azure SQL Database Security](https://docs.microsoft.com/azure/azure-sql/database/security-overview)
- [Git Filter-Repo Documentation](https://github.com/newren/git-filter-repo)

---

## Security Contact

For security issues or questions, contact: [Your Security Team Email]

**For security vulnerabilities**, please report them privately rather than opening public issues.

