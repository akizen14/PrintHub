# Quick Deploy to Render

This is a step-by-step guide to deploy PrintHub to Render in under 10 minutes.

## Prerequisites

- A [Render](https://render.com) account (free tier available)
- PrintHub code on GitHub

## Step 1: Prepare Your Repository

1. **Fork or Clone** this repository to your GitHub account
2. Ensure the following files are present:
   - `render.yaml` (deployment configuration)
   - `backend/requirements-cloud.txt` (Python dependencies)
   - `web/package.json` (Node.js dependencies)

## Step 2: Create New Blueprint on Render

1. **Log in** to [Render Dashboard](https://dashboard.render.com)
2. Click **"New"** → **"Blueprint"**
3. **Connect your GitHub repository**
   - Authorize Render to access your GitHub
   - Select the PrintHub repository
4. Render will automatically detect `render.yaml`
5. Click **"Apply"** to create services

## Step 3: Configure Environment Variables

### Backend Service Environment Variables

In the Render dashboard, go to your backend service and add:

| Variable | Value | Description |
|----------|-------|-------------|
| `CORS_ORIGINS` | `https://your-frontend.onrender.com` | Replace with actual frontend URL |
| `DATA_DIR` | `/opt/render/project/src/data` | Data persistence path |

**Note:** After frontend deploys, update `CORS_ORIGINS` with the actual URL.

### Frontend Service Environment Variables

Go to your frontend service and add:

| Variable | Value | Description |
|----------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.onrender.com` | Replace with actual backend URL |

**Note:** Get the backend URL from Render dashboard after backend deploys.

## Step 4: Wait for Deployment

- **Backend**: Takes ~5 minutes to build and deploy
- **Frontend**: Takes ~7 minutes to build and deploy

Monitor progress in the Render dashboard. Check logs if there are errors.

## Step 5: Update Environment Variables

After both services are deployed:

1. **Get the backend URL** (e.g., `https://printhub-backend.onrender.com`)
2. **Update frontend** `NEXT_PUBLIC_API_URL` with backend URL
3. **Redeploy frontend** (click "Manual Deploy" → "Deploy latest commit")

4. **Get the frontend URL** (e.g., `https://printhub-web.onrender.com`)
5. **Update backend** `CORS_ORIGINS` with frontend URL
6. **Redeploy backend** (click "Manual Deploy" → "Deploy latest commit")

## Step 6: Seed Initial Data

After deployment completes:

```bash
curl -X POST https://your-backend.onrender.com/seed
```

Or visit in browser: `https://your-backend.onrender.com/seed`

This creates:
- 2 demo printers
- 4 sample orders
- Default rates
- Admin password: `printhub2025`

## Step 7: Test Your Application

1. **Visit frontend**: `https://your-frontend.onrender.com`
2. **Create a test order**
3. **Check API docs**: `https://your-backend.onrender.com/docs`
4. **Verify health**: `https://your-backend.onrender.com/health`

## Step 8: Update CORS (Optional but Recommended)

For better security, update CORS to only allow your frontend:

1. Go to backend service in Render dashboard
2. Update `CORS_ORIGINS` to exact frontend URL: `https://printhub-web.onrender.com`
3. Click "Save Changes"

## Troubleshooting

### Service Won't Start

**Check logs**:
1. Go to service in Render dashboard
2. Click "Logs" tab
3. Look for error messages

Common issues:
- Missing environment variables
- Incorrect Python/Node version
- Build command failed

### Frontend Can't Connect to Backend

1. Verify `NEXT_PUBLIC_API_URL` is set correctly
2. Check backend is running and accessible
3. Test backend directly: `curl https://your-backend.onrender.com/health`
4. Rebuild frontend after changing env vars

### CORS Errors

1. Check `CORS_ORIGINS` includes your frontend URL
2. Ensure no trailing slashes in URLs
3. Try wildcard (`*`) for testing, then restrict to specific URL

### Data Not Persisting

1. Verify persistent disk is created (Check "Disks" in dashboard)
2. Ensure disk is mounted to `/opt/render/project/src/data`
3. Check `DATA_DIR` environment variable matches mount path

## Free Tier Limitations

Render's free tier:
- ✅ 750 hours/month free compute
- ✅ Automatic HTTPS
- ✅ Continuous deployment from Git
- ⚠️ Services spin down after 15 min inactivity
- ⚠️ First request after spin down takes 30-60 seconds

**Upgrade to paid plan** for:
- Always-on services
- No spin down delays
- More compute resources
- Priority support

## Next Steps

1. **Change admin password** (see [DEPLOYMENT.md](DEPLOYMENT.md))
2. **Update pricing rates**
3. **Set up custom domain** (optional)
4. **Configure backups**
5. **Monitor usage** in Render dashboard

## Support

- 📖 [Full Deployment Guide](DEPLOYMENT.md)
- 📖 [Render Documentation](https://render.com/docs)
- 🐛 [Report Issues](https://github.com/akizen14/PrintHub/issues)

---

**Estimated Time**: 10-15 minutes

**Status**: ✅ Ready for Production (with proper configuration)
