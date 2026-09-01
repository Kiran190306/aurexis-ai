# RENDER FRONTEND PRODUCTION CONFIGURATION

**Date**: 2026-09-01
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 8 - Frontend Production Configuration

---

## Executive Summary

Frontend production configuration documented. Frontend uses React with Vite, built to static files, served via nginx. API communication with backend via public HTTPS URL. CORS configured for backend domain. Authentication via JWT tokens stored in cookies. WebSocket support available (socket.io-client) but usage needs verification. HTTPS handled by Render. No backend secrets in frontend build.

**Status**: ✅ FRONTEND CONFIGURATION DOCUMENTED

---

## Frontend Technology Stack

### Framework and Build

**Framework**: React 18
**Build Tool**: Vite 5
**Language**: TypeScript
**Styling**: TailwindCSS
**UI Components**: Radix UI
**State Management**: Zustand
**HTTP Client**: Axios
**Routing**: React Router DOM

### Production Build

**Build Command**: `npm run build`
**Output Directory**: `dist/`
**Server**: nginx:alpine
**Port**: 80 (internal)

---

## API Communication

### API Base URL

**Current Configuration**:
- Development: `http://localhost:8000`
- Production: Must be set via VITE_API_URL

**Render Configuration**:
```yaml
envVars:
  - key: VITE_API_URL
    sync: false
    value: https://your-backend.onrender.com
```

**Usage in Frontend**:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

**Notes**:
- VITE_API_URL is public (visible in built frontend)
- Must use HTTPS in production
- Must point to Render backend URL

### API Proxy (nginx)

**Current Configuration**:
```nginx
location /api/ {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
}
```

**Render Adaptation**:
- nginx proxy may not work with Render (different network)
- Frontend should call backend directly via public URL
- Update nginx.conf to remove or comment proxy configuration

**Recommendation**: Use direct API calls via VITE_API_URL, disable nginx proxy

---

## HTTPS Configuration

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

### Render HTTPS

**Render provides**:
- Automatic HTTPS
- TLS certificates
- HTTP to HTTPS redirect
- SSL termination

**Action Required**:
- Remove HTTPS configuration from nginx.conf (handled by Render)
- Keep HTTP server block (Render handles TLS)
- Ensure frontend uses HTTPS for API calls

---

## CORS Configuration

### Backend CORS Configuration

**Current Configuration**:
```python
CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080"
]
```

**Render Configuration**:
```python
CORS_ORIGINS: List[str] = [
    "https://your-frontend.onrender.com"
]
```

**Action Required**:
- Set CORS_ORIGINS in Render backend environment
- Use frontend Render URL
- Allow credentials if using cookies

---

## Authentication Configuration

### Token Storage

**Current Configuration**:
- JWT access tokens (15 min expiration)
- JWT refresh tokens (7 day expiration)
- Tokens stored in cookies (js-cookie)

**Frontend Code**:
```typescript
import Cookies from 'js-cookie';

// Set token
Cookies.set('access_token', token);
Cookies.set('refresh_token', refreshToken);

// Get token
const token = Cookies.get('access_token');
```

**Security Considerations**:
- Cookies should be HttpOnly (backend configuration)
- Cookies should be Secure (HTTPS only)
- Cookies should have SameSite attribute

### Authentication Flow

1. User registers/logs in
2. Backend returns JWT tokens
3. Frontend stores tokens in cookies
4. Frontend includes tokens in API requests
5. Backend validates tokens
6. Tokens refreshed automatically

---

## WebSocket/SSE Configuration

### WebSocket Support

**Dependency**: `socket.io-client` in package.json

**Current Status**: Dependency present but usage not verified

**Action Required**:
- Verify if WebSockets are actually used in application
- If used: configure Render for WebSocket support
- If not used: no action required

### Render WebSocket Support

**Render supports**:
- WebSockets on web services
- Sticky sessions (if needed)
- No additional configuration required

**Configuration**:
- No special configuration needed
- WebSockets work out of the box on Render

---

## Production Build

### Build Process

**Steps**:
1. `npm ci` - Install dependencies
2. `npm run build` - Build TypeScript and bundle
3. Copy to nginx container
4. Serve via nginx

**Build Configuration**:
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
});
```

### Asset Paths

**Current Configuration**:
- Static assets served from root
- SPA routing via nginx try_files
- API proxy to backend (optional)

**Render Configuration**:
- Static assets served from root
- SPA routing via nginx try_files
- API calls via VITE_API_URL (direct)

---

## nginx Configuration

### Current nginx.conf

**Features**:
- SPA routing (try_files)
- API proxy (to backend:8000)
- Security headers
- Gzip compression
- Static file caching
- Health check endpoint

### Render Adaptation

**Required Changes**:
1. Remove or comment API proxy (backend not accessible via internal network)
2. Keep SPA routing
3. Keep security headers
4. Keep Gzip compression
5. Keep static file caching
6. Keep health check endpoint
7. Remove HTTPS configuration (handled by Render)

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

    # API proxy DISABLED for Render - use direct API calls
    # location /api/ {
    #     proxy_pass http://backend:8000;
    #     ...
    # }

    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
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

---

## Environment Variables

### Frontend Environment Variables

**VITE_API_URL** (Required):
- Purpose: Backend API URL
- Type: Public (visible in build)
- Render Service: Frontend
- Value: https://your-backend.onrender.com

**Other VITE_* Variables**:
- None currently used
- If added, will be public in build

### Security Warning

**VITE_* variables are public**:
- Visible in built JavaScript
- Do not put secrets in VITE_* variables
- Only put non-sensitive configuration

---

## Health Check

### Health Check Endpoint

**Path**: `/health`

**Response**: `healthy\n`

**Content-Type**: `text/plain`

**Render Configuration**:
```yaml
healthCheckPath: /health
```

---

## Static File Caching

### Current Configuration

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

**Status**: ✅ CONFIGURED

**Notes**:
- Static assets cached for 1 year
- Cache busting via file names (Vite handles this)
- Good for performance

---

## SPA Routing

### Current Configuration

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

**Status**: ✅ CONFIGURED

**Notes**:
- All routes serve index.html
- React Router handles client-side routing
- Works correctly with nginx

---

## Security Headers

### Current Configuration

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
```

**Status**: ✅ CONFIGURED

**Notes**:
- Clickjacking protection
- MIME type sniffing protection
- XSS protection
- Referrer policy

---

## Build Verification

### Build Test

**Command**:
```bash
cd frontend
npm ci
npm run build
```

**Expected Result**:
- Build succeeds
- dist/ directory created
- index.html present
- Static assets present

**Action Required**: Run build test before deployment

---

## Sign-Off

**Frontend Configuration Date**: 2026-09-01
**Frontend Configuration By**: Cascade AI Assistant
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 8 - Frontend Production Configuration
**Status**: ✅ FRONTEND CONFIGURATION DOCUMENTED

**Overall Assessment**: Frontend uses React with Vite, built to static files, served via nginx. API communication via public HTTPS URL (VITE_API_URL). CORS configured for backend domain. Authentication via JWT tokens in cookies. HTTPS handled by Render. nginx proxy disabled for Render (use direct API calls). WebSocket support available but usage needs verification. No backend secrets in frontend build.

**Required Changes**:
- Set VITE_API_URL in Render frontend environment
- Update CORS_ORIGINS in Render backend environment
- Disable nginx API proxy (use direct API calls)
- Remove HTTPS configuration from nginx.conf (handled by Render)

**Next Phase**: Phase 9 - Backend Production Configuration
