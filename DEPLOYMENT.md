# PrintHub Deployment Guide

This guide explains how to deploy PrintHub to Render or other cloud platforms.

## Table of Contents
- [Quick Deploy to Render](#quick-deploy-to-render)
- [Manual Deployment](#manual-deployment)
- [Environment Variables](#environment-variables)
- [Post-Deployment Steps](#post-deployment-steps)
- [Troubleshooting](#troubleshooting)

## Quick Deploy to Render

Render is a modern cloud platform that makes deployment simple. PrintHub includes a `render.yaml` configuration file for easy deployment.

### Prerequisites

1. A [Render](https://render.com) account (free tier available)
2. Your PrintHub repository on GitHub

### Deployment Steps

1. **Fork or Push to GitHub**
   - Ensure your PrintHub code is in a GitHub repository

2. **Create New Blueprint on Render**
   - Log in to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` file

3. **Configure Environment Variables**
   
   For the **Backend Service**:
   - `CORS_ORIGINS`: Set to your frontend URL (e.g., `https://your-app.onrender.com`)
   - `DATA_DIR`: Leave as default `/opt/render/project/src/data`
   
   For the **Frontend Service**:
   - `NEXT_PUBLIC_API_URL`: Set to your backend URL (e.g., `https://printhub-backend.onrender.com`)

4. **Deploy**
   - Click "Apply" to deploy both services
   - Wait for build and deployment to complete (5-10 minutes)

5. **Seed Initial Data**
   - After deployment, visit: `https://your-backend.onrender.com/seed`
   - Or use curl: `curl -X POST https://your-backend.onrender.com/seed`

6. **Access Your Application**
   - Frontend: `https://your-frontend.onrender.com`
   - Backend API: `https://your-backend.onrender.com`
   - API Docs: `https://your-backend.onrender.com/docs`

### Note on Free Tier

Render's free tier spins down inactive services after 15 minutes. The first request after spin-down will take 30-60 seconds. For production use, consider upgrading to a paid plan.

## Manual Deployment

If you're deploying to another platform (Heroku, DigitalOcean, AWS, etc.), follow these steps:

### Backend Deployment

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   export CORS_ORIGINS="https://your-frontend-url.com"
   export DATA_DIR="/path/to/persistent/storage/data"
   export PORT=8000
   ```

3. **Start the Server**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

### Frontend Deployment

1. **Install Dependencies**
   ```bash
   cd web
   npm install
   ```

2. **Set Environment Variables**
   ```bash
   export NEXT_PUBLIC_API_URL="https://your-backend-url.com"
   ```

3. **Build for Production**
   ```bash
   npm run build
   ```

4. **Start the Server**
   ```bash
   npm start
   ```

## Environment Variables

### Backend Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated or `*`) | `http://localhost:3000,http://localhost:3001` | No |
| `DATA_DIR` | Directory for JSON database files | `./data` | No |
| `PORT` | Port for the backend server | `8000` | No |

Example `.env` file for backend:
```bash
CORS_ORIGINS=https://printhub-web.onrender.com
DATA_DIR=/opt/render/project/src/data
```

### Frontend Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` | Yes |
| `PORT` | Port for the frontend server | `3000` | No |

Example `.env` file for frontend:
```bash
NEXT_PUBLIC_API_URL=https://printhub-backend.onrender.com
```

**Note**: Environment variables prefixed with `NEXT_PUBLIC_` are exposed to the browser. Never put secrets in these variables.

## Post-Deployment Steps

### 1. Seed Initial Data

After first deployment, seed the database with initial data:

```bash
curl -X POST https://your-backend-url.onrender.com/seed
```

This creates:
- 2 demo printers (Laser-A4, ColorPro)
- 4 sample orders
- Default pricing rates
- Admin credentials (password: `printhub2025`)

### 2. Change Admin Password

For security, change the default admin password:

```python
import hashlib
new_password = "your_secure_password"
hash_value = hashlib.sha256(new_password.encode()).hexdigest()
print(hash_value)
```

Then update via API:
```bash
curl -X PUT https://your-backend-url.com/settings \
  -H "Content-Type: application/json" \
  -d '{
    "adminPassHash": "YOUR_HASH_HERE",
    "thresholds": {
      "smallPages": 15,
      "chunkPages": 100,
      "agingMinutes": 12
    }
  }'
```

### 3. Configure Pricing

Update pricing to match your needs:

```bash
curl -X PUT https://your-backend-url.com/rates \
  -H "Content-Type: application/json" \
  -d '{
    "bwSingleA4": 1.5,
    "bwDuplexA4": 1.0,
    "colorSingleA4": 6.0,
    "colorDuplexA4": 5.0,
    "minCharge": 10.0,
    "effectiveDate": 1730000000
  }'
```

### 4. Test the Application

1. Visit your frontend URL
2. Create a test order
3. Complete payment flow
4. Verify order appears in the system

## Data Persistence

### Render Persistent Disk

The `render.yaml` file includes a persistent disk configuration for the backend:

```yaml
disk:
  name: printhub-data
  mountPath: /opt/render/project/src/data
  sizeGB: 1
```

This ensures your orders, printers, and settings persist across deployments.

### Backup Strategy

For production use, implement regular backups:

1. **Manual Backup**: Download JSON files from `/data` directory
2. **Automated Backup**: Set up a cron job to copy files to external storage
3. **Database Export**: Use the API to export data periodically

Example backup script:
```bash
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
curl https://your-backend-url.com/orders > $BACKUP_DIR/orders.json
curl https://your-backend-url.com/printers > $BACKUP_DIR/printers.json
curl https://your-backend-url.com/rates > $BACKUP_DIR/rates.json
```

## Troubleshooting

### CORS Errors

**Problem**: Frontend shows CORS errors when calling API

**Solution**: Ensure `CORS_ORIGINS` environment variable in backend includes your frontend URL:
```bash
CORS_ORIGINS=https://your-frontend.onrender.com
```

Or use wildcard for testing (not recommended for production):
```bash
CORS_ORIGINS=*
```

### API URL Not Updating

**Problem**: Frontend still uses `localhost:8000` after deployment

**Solution**: 
1. Ensure `NEXT_PUBLIC_API_URL` is set in frontend environment variables
2. Rebuild frontend after changing environment variables:
   ```bash
   npm run build
   ```

### Service Spin Down (Render Free Tier)

**Problem**: First request takes 30+ seconds

**Solution**: 
- This is expected on Render's free tier
- Upgrade to paid plan for always-on services
- Or implement a "keep-alive" ping service

### Data Not Persisting

**Problem**: Data lost after redeployment

**Solution**:
1. Verify persistent disk is attached (Render dashboard)
2. Check `DATA_DIR` points to the mounted disk path
3. Ensure disk is at least 1GB

### Build Failures

**Backend Build Fails**:
- Check Python version (requires 3.8+)
- Verify all dependencies in `requirements.txt`
- Check build logs for specific errors

**Frontend Build Fails**:
- Check Node.js version (requires 18+)
- Clear cache: `npm cache clean --force`
- Delete `node_modules` and reinstall

## Production Considerations

### Security

1. **Change Default Password**: Never use `printhub2025` in production
2. **HTTPS Only**: Ensure both services use HTTPS
3. **Environment Variables**: Never commit `.env` files
4. **API Rate Limiting**: Consider adding rate limiting middleware

### Performance

1. **Caching**: Frontend API calls are cached for 5 seconds
2. **Compression**: Backend uses GZIP compression
3. **Database**: TinyDB works well for small-medium loads (<10k orders)
4. **Monitoring**: Use Render's built-in metrics or add custom monitoring

### Scaling

For high-traffic scenarios, consider:
1. **Database**: Migrate from TinyDB to PostgreSQL or MongoDB
2. **File Storage**: Use S3 or similar for uploaded files
3. **Caching**: Add Redis for caching
4. **Load Balancing**: Deploy multiple backend instances

## Alternative Deployment Platforms

### Heroku

1. Create `Procfile` for backend:
   ```
   web: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

2. Create `Procfile` for frontend:
   ```
   web: cd web && npm start
   ```

3. Deploy using Heroku CLI or GitHub integration

### DigitalOcean App Platform

1. Create `app.yaml` configuration
2. Deploy via GitHub integration
3. Configure environment variables in dashboard

### AWS Elastic Beanstalk

1. Create application configuration
2. Upload zipped application
3. Configure environment in AWS console

### Docker Deployment

See [DOCKER.md](DOCKER.md) for containerized deployment (create this file if needed).

## Support

For deployment issues:
1. Check application logs in your hosting dashboard
2. Review this guide and [README.md](README.md)
3. Check API docs at `/docs` endpoint
4. Verify environment variables are set correctly

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [TinyDB Documentation](https://tinydb.readthedocs.io/)

---

**Need Help?** Open an issue on GitHub or check the troubleshooting section.
