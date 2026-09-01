# RENDER HTTPS CUSTOM DOMAIN CONFIGURATION

**Date**: 2026-09-01
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 14 - HTTPS/Custom Domain Configuration

---

## Executive Summary

HTTPS and custom domain configuration documented. Render provides automatic HTTPS with TLS certificates for all services. HTTP to HTTPS redirect automatic. Custom domain optional (can use Render-generated URL). nginx HTTPS configuration removed (handled by Render). Secure cookies and CORS configured for HTTPS. HSTS recommended after testing. No manual certificate management required.

**Status**: ✅ HTTPS CONFIGURATION DOCUMENTED

---

## Render HTTPS

### Automatic HTTPS

**Render Feature**: Automatic HTTPS for all web services

**How It Works**:
1. Deploy service to Render
2. Render generates HTTPS URL: `https://service-name.onrender.com`
3. Render provisions TLS certificate (Let's Encrypt)
4. Render handles certificate renewal
5. Automatic HTTP to HTTPS redirect

**No Action Required**: HTTPS is automatic on Render

### TLS Certificates

**Certificate Authority**: Let's Encrypt

**Certificate Type**: DV (Domain Validation)

**Validity**: 90 days (auto-renewed)

**Renewal**: Automatic (no action required)

### HTTP to HTTPS Redirect

**Automatic**: Yes

**Configuration**: Render handles redirect

**nginx Configuration**: Remove HTTP redirect from nginx.conf (handled by Render)

---

## Custom Domain Configuration

### Custom Domain (Optional)

**Purpose**: Use custom domain instead of Render-generated URL

**Example**: `https://jarvis-ai.example.com` instead of `https://jarvis-frontend.onrender.com`

### Custom Domain Setup

**Prerequisites**:
- Own domain name
- DNS provider access

**Steps**:
1. Go to Render dashboard
2. Navigate to service (frontend or backend)
3. Click "Settings"
4. Click "Custom Domains"
5. Add custom domain
6. Configure DNS records
7. Verify DNS propagation
8. Wait for TLS certificate provision

### DNS Records

**Required DNS Records**:

**A Record** (for apex domain):
```
Type: A
Name: @
Value: Render service IP
TTL: 300
```

**CNAME Record** (for subdomain):
```
Type: CNAME
Name: www
Value: Render service URL
TTL: 300
```

**Example**:
```
Type: CNAME
Name: jarvis-ai
Value: jarvis-frontend.onrender.com
TTL: 300
```

### DNS Propagation

**Time**: 5 minutes to 48 hours (typically 1-2 hours)

**Verification**:
```bash
nslookup jarvis-ai.example.com
dig jarvis-ai.example.com
```

---

## nginx Configuration Updates

### Current nginx Configuration

**HTTP Server**:
```nginx
server {
    listen 80;
    server_name localhost;
    # HTTP fallback
}
```

**HTTPS Server** (commented):
```nginx
server {
    listen 443 ssl http2;
    server_name localhost;
    # SSL configuration
}
```

### Render Adaptation

**Required Changes**:
1. Remove HTTPS server block (handled by Render)
2. Keep HTTP server block (Render handles TLS)
3. Remove HTTP redirect (handled by Render)
4. Keep security headers
5. Keep SPA routing
6. Keep static file caching

**Updated nginx.conf**:
```nginx
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript application/json;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1r;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

**Note**: HTTPS server block removed (handled by Render)

---

## Secure Cookies

### Cookie Configuration

**Backend Configuration**:
```python
# Cookie settings
COOKIE_SECURE = True  # HTTPS only
COOKIE_HTTPONLY = True  # Not accessible via JavaScript
COOKIE_SAMESITE = 'Lax'  # CSRF protection
```

**Render Configuration**:
```yaml
envVars:
  - key: COOKIE_SECURE
    value: true
  - key: COOKIE_HTTPONLY
    value: true
  - key: COOKIE_SAMESITE
    value: Lax
```

**Note**: Cookies must be secure (HTTPS only) in production

---

## CORS Configuration

### CORS with HTTPS

**Backend Configuration**:
```python
CORS_ORIGINS: List[str] = [
    "https://your-frontend.onrender.com"
]
```

**Custom Domain**:
```python
CORS_ORIGINS: List[str] = [
    "https://jarvis-ai.example.com"
]
```

**Render Configuration**:
```yaml
envVars:
  - key: CORS_ORIGINS
    sync: false
    value: https://jarvis-ai.example.com
```

**Note**: Must use HTTPS URLs in CORS origins

---

## HSTS Configuration

### HTTP Strict Transport Security

**Purpose**: Force HTTPS for all future requests

**Configuration**:
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

**Implementation**:
1. Initially deploy without HSTS
2. Verify HTTPS works correctly
3. Enable HSTS after testing
4. Start with max-age=86400 (1 day)
5. Increase to max-age=31536000 (1 year) after validation

**Warning**: HSTS can cause issues if HTTPS is not working correctly

**Recommendation**: Enable HSTS after 1 week of successful HTTPS operation

---

## Frontend API Configuration

### API URL Configuration

**Current Configuration**:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

**Render Configuration**:
```yaml
envVars:
  - key: VITE_API_URL
    sync: false
    value: https://your-backend.onrender.com
```

**Custom Domain**:
```yaml
envVars:
  - key: VITE_API_URL
    sync: false
    value: https://api.jarvis-ai.example.com
```

**Note**: Must use HTTPS URL in production

---

## URL Examples

### Render-Generated URLs

**Frontend**: `https://jarvis-frontend.onrender.com`
**Backend**: `https://jarvis-backend.onrender.com`

### Custom Domain URLs

**Frontend**: `https://jarvis-ai.example.com`
**Backend**: `https://api.jarvis-ai.example.com`

### Subdomain Configuration

**Frontend**: `https://app.jarvis-ai.example.com`
**Backend**: `https://api.jarvis-ai.example.com`

---

## SSL/TLS Configuration

### TLS Version

**Render Default**: TLS 1.2 and TLS 1.3

**Configuration**: Automatic (no action required)

**Note**: TLS 1.0 and 1.1 disabled by Render

### Cipher Suites

**Render Default**: Modern cipher suites

**Configuration**: Automatic (no action required)

**Note**: Weak ciphers disabled by Render

---

## HTTPS Verification

### Verification Steps

**1. Check HTTPS Works**:
```bash
curl -I https://your-service.onrender.com
```

**Expected**: HTTP/2 200 with SSL/TLS

**2. Check Certificate**:
```bash
openssl s_client -connect your-service.onrender.com:443 -servername your-service.onrender.com
```

**Expected**: Valid certificate from Let's Encrypt

**3. Check Redirect**:
```bash
curl -I http://your-service.onrender.com
```

**Expected**: 301/302 redirect to HTTPS

**4. Check HSTS** (if enabled):
```bash
curl -I https://your-service.onrender.com
```

**Expected**: Strict-Transport-Security header present

---

## Troubleshooting

### HTTPS Not Working

**Symptoms**:
- HTTPS not accessible
- Certificate error
- Mixed content warning

**Possible Causes**:
1. DNS not propagated
2. Certificate not provisioned
3. Mixed content (HTTP resources)
4. CORS misconfiguration

**Solutions**:
1. Wait for DNS propagation
2. Wait for certificate provision (up to 24 hours)
3. Fix mixed content (use HTTPS for all resources)
4. Fix CORS configuration

### Custom Domain Not Working

**Symptoms**:
- Custom domain not accessible
- DNS resolution fails
- Certificate error for custom domain

**Possible Causes**:
1. DNS records incorrect
2. DNS not propagated
3. Certificate not provisioned for custom domain

**Solutions**:
1. Verify DNS records
2. Wait for DNS propagation
3. Wait for certificate provision (up to 24 hours)

### Mixed Content Warning

**Symptoms**:
- Browser shows mixed content warning
- Some resources loaded over HTTP

**Possible Causes**:
1. Hardcoded HTTP URLs in code
2. API calls using HTTP
3. Static assets using HTTP

**Solutions**:
1. Replace HTTP with HTTPS in code
2. Use relative URLs
3. Use HTTPS for all resources

---

## Sign-Off

**HTTPS Configuration Date**: 2026-09-01
**HTTPS Configuration By**: Cascade AI Assistant
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 14 - HTTPS/Custom Domain Configuration
**Status**: ✅ HTTPS CONFIGURATION DOCUMENTED

**Overall Assessment**: Render provides automatic HTTPS with TLS certificates (Let's Encrypt). HTTP to HTTPS redirect automatic. Custom domain optional (can use Render-generated URL). nginx HTTPS configuration removed (handled by Render). Secure cookies and CORS configured for HTTPS. HSTS recommended after testing. No manual certificate management required.

**Required Configuration**:
- Remove HTTPS server block from nginx.conf
- Set CORS_ORIGINS to HTTPS URL
- Set VITE_API_URL to HTTPS URL
- Configure secure cookies

**Optional Configuration**:
- Configure custom domain (DNS records)
- Enable HSTS after testing
- Configure subdomains

**Next Phase**: Phase 15 - Security Check
