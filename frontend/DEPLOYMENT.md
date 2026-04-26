# ClipPilot Lite Frontend - Deployment Guide

This guide covers deploying the ClipPilot Lite frontend to various platforms.

## Table of Contents

- [Vercel (Recommended)](#vercel-recommended)
- [Docker](#docker)
- [Manual Deployment](#manual-deployment)
- [Environment Configuration](#environment-configuration)
- [Troubleshooting](#troubleshooting)

## Vercel (Recommended)

Vercel is the easiest way to deploy Next.js applications.

### Quick Start

1. **Push code to GitHub**:
   ```bash
   git add .
   git commit -m "Initial frontend commit"
   git push origin main
   ```

2. **Connect to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Sign in with GitHub
   - Click "New Project"
   - Select the clippilot repository
   - Click "Import"

3. **Configure environment variables**:
   - In the "Environment Variables" section, add:
     - `NEXT_PUBLIC_SUPABASE_URL` = Your Supabase URL
     - `NEXT_PUBLIC_SUPABASE_ANON_KEY` = Your Supabase anon key
     - `NEXT_PUBLIC_API_URL` = Backend API URL (e.g., `https://api.example.com`)

4. **Deploy**:
   - Click "Deploy"
   - Vercel will build and deploy automatically

### Automatic Deployments

Vercel automatically redeploys when you:
- Push to your main branch
- Create a pull request (preview deployment)

### Custom Domain

1. Go to project settings
2. Click "Domains"
3. Add your custom domain
4. Follow DNS configuration instructions

## Docker

Deploy Docker containers to any cloud provider (AWS, Google Cloud, Azure, DigitalOcean, etc.).

### Build Docker Image

```bash
# From the frontend directory
docker build -t clippilot-frontend:latest .
```

### Run Locally

```bash
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co \
  -e NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key \
  -e NEXT_PUBLIC_API_URL=http://backend:8000 \
  clippilot-frontend:latest
```

### Push to Registry

#### Docker Hub

```bash
# Build with tag
docker build -t yourusername/clippilot-frontend:latest .

# Log in
docker login

# Push
docker push yourusername/clippilot-frontend:latest
```

#### GitHub Container Registry (GHCR)

```bash
# Build with tag
docker build -t ghcr.io/yourusername/clippilot-frontend:latest .

# Log in (requires GitHub token)
echo $GITHUB_TOKEN | docker login ghcr.io -u yourusername --password-stdin

# Push
docker push ghcr.io/yourusername/clippilot-frontend:latest
```

### Deploy to AWS ECS

1. Create ECR repository:
   ```bash
   aws ecr create-repository --repository-name clippilot-frontend --region us-east-1
   ```

2. Push image:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   docker tag clippilot-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/clippilot-frontend:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/clippilot-frontend:latest
   ```

3. Create ECS task definition with:
   - Image: `<account-id>.dkr.ecr.us-east-1.amazonaws.com/clippilot-frontend:latest`
   - Port: 3000
   - Environment variables as above

4. Create ECS service and load balancer

### Deploy to Google Cloud Run

```bash
# Configure Docker to push to GCR
gcloud auth configure-docker

# Build and tag
docker build -t gcr.io/your-project/clippilot-frontend:latest .

# Push to GCR
docker push gcr.io/your-project/clippilot-frontend:latest

# Deploy
gcloud run deploy clippilot-frontend \
  --image gcr.io/your-project/clippilot-frontend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars NEXT_PUBLIC_SUPABASE_URL=...,NEXT_PUBLIC_SUPABASE_ANON_KEY=...,NEXT_PUBLIC_API_URL=...
```

### Docker Compose (for local development with backend)

Create `docker-compose.yml` in the project root:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:password@db:5432/clippilot
      SUPABASE_URL: https://your-project.supabase.co
      SUPABASE_KEY: your-key
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_SUPABASE_URL: https://your-project.supabase.co
      NEXT_PUBLIC_SUPABASE_ANON_KEY: your-anon-key
      NEXT_PUBLIC_API_URL: http://backend:8000
    depends_on:
      - backend

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: clippilot
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

Run with:
```bash
docker-compose up
```

## Manual Deployment

### VPS (Ubuntu/Debian)

1. **Install Node.js 18+**:
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

2. **Clone repository**:
   ```bash
   git clone https://github.com/yourusername/clippilot.git
   cd clippilot/frontend
   ```

3. **Install dependencies**:
   ```bash
   npm ci
   ```

4. **Build**:
   ```bash
   npm run build
   ```

5. **Install PM2** (process manager):
   ```bash
   sudo npm install -g pm2
   ```

6. **Create ecosystem config** (`ecosystem.config.js`):
   ```javascript
   module.exports = {
     apps: [{
       name: 'clippilot-frontend',
       script: 'npm start',
       instances: 'max',
       exec_mode: 'cluster',
       env: {
         NODE_ENV: 'production',
         NEXT_PUBLIC_SUPABASE_URL: 'https://your-project.supabase.co',
         NEXT_PUBLIC_SUPABASE_ANON_KEY: 'your-anon-key',
         NEXT_PUBLIC_API_URL: 'https://api.example.com',
       }
     }]
   }
   ```

7. **Start with PM2**:
   ```bash
   pm2 start ecosystem.config.js
   pm2 save
   pm2 startup
   ```

8. **Setup Nginx reverse proxy**:
   ```nginx
   server {
     listen 80;
     server_name your-domain.com;

     location / {
       proxy_pass http://localhost:3000;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection 'upgrade';
       proxy_set_header Host $host;
       proxy_cache_bypass $http_upgrade;
     }
   }
   ```

9. **Setup SSL with Certbot**:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

## Environment Configuration

### Production Environment Variables

```bash
# Required
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-from-supabase
NEXT_PUBLIC_API_URL=https://api.example.com

# Optional
NODE_ENV=production
```

### Security Best Practices

1. **Never commit `.env.local`** to git
2. **Use environment variable secrets** in CI/CD
3. **Rotate keys regularly** in Supabase dashboard
4. **Enable CORS properly** in backend for your domain
5. **Use HTTPS** for production
6. **Keep dependencies updated**: `npm audit fix`

## Monitoring and Logging

### Vercel
- Built-in analytics at vercel.com/analytics
- Real-time logs: `vercel logs`
- Custom monitoring: integrate with Sentry, LogRocket, etc.

### Docker/VPS
- Use `pm2 logs` to view application logs
- Setup log rotation with `pm2 logrotate`
- Integrate with centralized logging (ELK, Datadog, etc.)

### Add Sentry Error Tracking

```bash
npm install @sentry/nextjs
```

In `next.config.js`:
```javascript
const withSentryConfig = require("@sentry/nextjs/cjs/withSentryConfig");

const nextConfig = {
  // ... your config
};

module.exports = withSentryConfig(nextConfig, {
  org: "your-org",
  project: "clippilot-frontend",
});
```

## Troubleshooting

### Build Fails

**"Cannot find module"**:
- Clear node_modules: `rm -rf node_modules package-lock.json`
- Reinstall: `npm ci`

**TypeScript errors**:
- Run type check: `npm run type-check`
- Check for missing type definitions

### Runtime Errors

**CORS errors**:
- Check backend CORS configuration
- Verify `NEXT_PUBLIC_API_URL` matches backend origin

**Supabase connection fails**:
- Verify credentials in `.env.local`
- Check Supabase project status
- Ensure anon key has correct permissions

**Videos not displaying**:
- Check Supabase storage bucket permissions
- Verify image domains in `next.config.js`

### Performance Issues

**Slow page loads**:
- Check Network tab in browser DevTools
- Optimize images with `next/image`
- Enable caching headers

**High CPU usage**:
- Monitor with `top` (Linux) or Task Manager (Windows)
- Scale horizontally with load balancer
- Profile with `next/built-in-profiling`

## Rollback

### Vercel
- Deployments tab shows previous versions
- Click to redeploy previous version instantly

### Docker
```bash
docker run -p 3000:3000 clippilot-frontend:previous-tag
```

### VPS with PM2
```bash
pm2 status
pm2 restart clippilot-frontend
pm2 save
```

## Next Steps

1. Setup CI/CD pipeline (GitHub Actions, GitLab CI)
2. Configure monitoring and alerting
3. Setup automated backups
4. Create runbook for common issues
5. Setup staging environment for testing

## Support

For deployment issues, check:
- [Next.js Deployment Docs](https://nextjs.org/docs/deployment)
- [Vercel Documentation](https://vercel.com/docs)
- Backend README: `../backend/DEPLOYMENT.md`
