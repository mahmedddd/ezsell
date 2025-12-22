# Deployment Guide

This guide covers deploying EZSell to production environments.

## 🚀 Deployment Options

### 1. Backend Deployment

#### Option A: Railway/Render (Easiest)

1. **Railway**:
   ```bash
   # Install Railway CLI
   npm i -g @railway/cli
   
   # Login
   railway login
   
   # Deploy from backend directory
   cd ezsell/ezsell/backend
   railway init
   railway up
   ```

2. **Render**:
   - Connect your GitHub repository
   - Select `ezsell/ezsell/backend` as root directory
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### Option B: AWS EC2

1. **Launch EC2 Instance**:
   - Ubuntu 22.04 LTS
   - t2.small or larger
   - Security group: Allow ports 22, 80, 443, 8000

2. **Setup Server**:
   ```bash
   # Connect to EC2
   ssh -i your-key.pem ubuntu@your-ip
   
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install dependencies
   sudo apt install python3.10 python3-pip nginx -y
   
   # Clone repository
   git clone https://github.com/mahmedddd/ezsell.git
   cd ezsell/ezsell/ezsell/backend
   
   # Setup virtual environment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Create systemd service
   sudo nano /etc/systemd/system/ezsell.service
   ```

3. **Systemd Service** (`/etc/systemd/system/ezsell.service`):
   ```ini
   [Unit]
   Description=EZSell Backend
   After=network.target
   
   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/ezsell/ezsell/ezsell/backend
   Environment="PATH=/home/ubuntu/ezsell/ezsell/ezsell/backend/venv/bin"
   ExecStart=/home/ubuntu/ezsell/ezsell/ezsell/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **Start Service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable ezsell
   sudo systemctl start ezsell
   sudo systemctl status ezsell
   ```

5. **Nginx Configuration** (`/etc/nginx/sites-available/ezsell`):
   ```nginx
   server {
       listen 80;
       server_name api.yourdomain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

6. **Enable Site**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/ezsell /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

7. **SSL with Let's Encrypt**:
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d api.yourdomain.com
   ```

#### Option C: Docker

1. **Create Dockerfile** (`backend/Dockerfile`):
   ```dockerfile
   FROM python:3.10-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   EXPOSE 8000
   
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Build and Run**:
   ```bash
   docker build -t ezsell-backend .
   docker run -p 8000:8000 ezsell-backend
   ```

### 2. Frontend Deployment

#### Option A: Vercel (Recommended)

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Deploy**:
   ```bash
   cd ezsell/ezsell/frontend
   vercel
   ```

3. **Environment Variables** (in Vercel dashboard):
   ```
   VITE_API_URL=https://api.yourdomain.com/api/v1
   VITE_BACKEND_URL=https://api.yourdomain.com
   ```

#### Option B: Netlify

1. **Build**:
   ```bash
   cd ezsell/ezsell/frontend
   npm run build
   ```

2. **Deploy**:
   ```bash
   npm i -g netlify-cli
   netlify deploy --prod
   ```

#### Option C: AWS S3 + CloudFront

1. **Build**:
   ```bash
   npm run build
   ```

2. **Create S3 Bucket**:
   - Enable static website hosting
   - Upload `dist` folder contents

3. **Setup CloudFront**:
   - Create distribution
   - Point to S3 bucket
   - Configure custom domain

### 3. Database

#### PostgreSQL Setup (Production)

1. **Install PostgreSQL**:
   ```bash
   sudo apt install postgresql postgresql-contrib -y
   ```

2. **Create Database**:
   ```bash
   sudo -u postgres psql
   CREATE DATABASE ezsell;
   CREATE USER ezselluser WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE ezsell TO ezselluser;
   \q
   ```

3. **Update Environment**:
   ```env
   DATABASE_URL=postgresql://ezselluser:your_password@localhost/ezsell
   ```

## 🔧 Production Configuration

### Backend Environment Variables

Create `.env` in production:
```env
# Production settings
DEBUG=false
RELOAD=false
PROJECT_NAME=EZSell
SECRET_KEY=your-super-secret-key-change-this
DATABASE_URL=postgresql://user:pass@host/dbname
FRONTEND_URL=https://yourdomain.com

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Google OAuth
GOOGLE_CLIENT_ID=your-production-client-id
GOOGLE_CLIENT_SECRET=your-production-client-secret
GOOGLE_REDIRECT_URI=https://api.yourdomain.com/api/v1/auth/google/callback

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Frontend Environment Variables

Create `.env.production`:
```env
VITE_API_URL=https://api.yourdomain.com/api/v1
VITE_BACKEND_URL=https://api.yourdomain.com
VITE_DEBUG=false
```

## 🔒 Security Checklist

- [ ] Change all default passwords and secret keys
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set up firewall (UFW, AWS Security Groups)
- [ ] Enable rate limiting
- [ ] Set up monitoring and logging
- [ ] Regular backups
- [ ] Keep dependencies updated
- [ ] Use environment variables for secrets
- [ ] Disable debug mode in production

## 📊 Monitoring

### Backend Monitoring

1. **Health Check Endpoint**:
   ```python
   @app.get("/health")
   def health_check():
       return {"status": "healthy", "timestamp": datetime.now()}
   ```

2. **Logging**:
   ```python
   import logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

### Frontend Monitoring

1. **Error Tracking**: Use Sentry
2. **Analytics**: Google Analytics or Plausible
3. **Performance**: Lighthouse CI

## 🔄 CI/CD Pipeline

### GitHub Actions Example

`.github/workflows/deploy.yml`:
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Railway
        run: |
          npm i -g @railway/cli
          railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Vercel
        run: |
          cd ezsell/ezsell/frontend
          npm install
          npx vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
```

## 📦 Database Migrations

For schema changes:

1. **Create Migration**:
   ```bash
   alembic revision -m "add new column"
   ```

2. **Apply Migration**:
   ```bash
   alembic upgrade head
   ```

## 🔙 Backup Strategy

### Database Backups

```bash
# PostgreSQL backup
pg_dump -U ezselluser ezsell > backup_$(date +%Y%m%d).sql

# Automated daily backups (crontab)
0 2 * * * pg_dump -U ezselluser ezsell > /backups/backup_$(date +\%Y\%m\%d).sql
```

### File Backups

```bash
# Backup uploads
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/

# Automated backups
0 3 * * * tar -czf /backups/uploads_$(date +\%Y\%m\%d).tar.gz /path/to/uploads/
```

## 🚨 Troubleshooting Production

### High CPU Usage
- Check number of uvicorn workers
- Enable connection pooling
- Add caching (Redis)

### Database Connection Issues
- Check connection pool settings
- Verify DATABASE_URL
- Check PostgreSQL max_connections

### Slow Response Times
- Enable CDN for static files
- Add database indexes
- Implement caching
- Optimize queries

## 📈 Scaling

### Horizontal Scaling
- Multiple backend instances behind load balancer
- Redis for session management
- CDN for static files

### Vertical Scaling
- Increase server resources
- Optimize database queries
- Add indexes

## ✅ Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrated
- [ ] SSL certificates installed
- [ ] Monitoring set up
- [ ] Backups configured
- [ ] Security audit complete
- [ ] Performance testing done
- [ ] Documentation updated
- [ ] Rollback plan ready

---

**Need Help?** Open an issue or contact the maintainers.
