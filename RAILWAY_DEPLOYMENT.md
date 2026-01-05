# Railway Deployment Guide

This guide will walk you through deploying your FastAPI backend to Railway step by step.

## Prerequisites

1. A Railway account (sign up at [railway.app](https://railway.app))
2. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. All environment variables ready

## Step-by-Step Deployment

### Step 1: Prepare Your Repository

1. Make sure all your changes are committed and pushed to your Git repository:
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push
   ```

### Step 2: Create a Railway Account and Project

1. Go to [railway.app](https://railway.app) and sign up/login
2. Click **"New Project"** in the dashboard
3. Select **"Deploy from GitHub repo"** (or GitLab/Bitbucket if you prefer)
4. Authorize Railway to access your repository
5. Select your `cabinrentals` repository

### Step 3: Configure the Service

1. Railway will detect your project. You need to configure it:
   - Click on your new service
   - Go to **Settings** tab
   - Set the **Root Directory** to `backend` (since your backend code is in the backend folder)
   - Railway will automatically detect it's a Python project

### Step 4: Set Environment Variables

1. In your Railway service, go to the **Variables** tab
2. Add all the environment variables your app needs. Based on your `config.py`, you'll need:

   **Required Variables:**
   ```
   SUPABASE_URL=https://cueenbvreqsnqwpajufv.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1ZWVuYnZyZXFzbnF3cGFqdWZ2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY1ODcxNDEsImV4cCI6MjA4MjE2MzE0MX0.wssHqwBGUFz3sbQ7A6zxli1R4lMTFgImn5iaUEdGvpg
   SECRET_KEY=my-secret-key-for-cabinrentals-of-georgia
   ENVIRONMENT=production
   DEBUG=False
   ```

   **CORS Origins (for your frontend):**
   ```
   CORS_ORIGINS=https://your-frontend-domain.com,http://localhost:3000
   ```
   Note: You can set CORS_ORIGINS as a comma-separated string (recommended) or as a JSON array string like `["https://your-frontend-domain.com","http://localhost:3000"]`

   **Optional Variables (if you use them):**
   ```
   GEMINI_API_KEY=your-key
   OPENAI_API_KEY=your-key
   CLAUDE_API_KEY=your-key
   STREAMLINE_API_URL=your-url
   STREAMLINE_API_KEY=your-key
   R2_ACCOUNT_ID=your-id
   R2_ACCESS_KEY_ID=your-key
   R2_SECRET_ACCESS_KEY=your-secret
   R2_BUCKET_NAME=your-bucket
   R2_PUBLIC_URL=your-url
   REDIS_URL=your-redis-url
   ```

3. **Important:** Generate a secure `SECRET_KEY` for production:
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

### Step 5: Configure Build Settings (Optional)

Railway will automatically:
- Detect Python from `requirements.txt`
- Install dependencies from `requirements.txt`
- Run the command from `Procfile`

If you need to customize:
1. Go to **Settings** → **Build**
2. You can override the build command if needed
3. The start command is already set in `Procfile`

### Step 6: Deploy

1. Railway will automatically start building and deploying when you:
   - Push new commits to your repository, OR
   - Click **"Deploy"** in the Railway dashboard

2. Watch the build logs in the **Deployments** tab
3. Wait for the deployment to complete (usually 2-5 minutes)

### Step 7: Get Your Application URL

1. Once deployed, Railway will provide a public URL
2. Go to **Settings** → **Networking**
3. You'll see your service URL (e.g., `https://your-app-name.up.railway.app`)
4. You can also set a custom domain if you have one

### Step 8: Verify Deployment

1. Test your health endpoint:
   ```
   https://your-app-name.up.railway.app/health
   ```
   Should return: `{"status": "ok", "version": "1.0.0"}`

2. Test your API docs:
   ```
   https://your-app-name.up.railway.app/api/docs
   ```

3. Test your root endpoint:
   ```
   https://your-app-name.up.railway.app/
   ```

### Step 9: Update CORS Origins

1. After getting your Railway URL, update the `CORS_ORIGINS` variable:
   ```
   CORS_ORIGINS=https://your-frontend-domain.com,https://your-app-name.up.railway.app
   ```
   Or as JSON:
   ```
   CORS_ORIGINS=["https://your-frontend-domain.com","https://your-app-name.up.railway.app"]
   ```
2. Redeploy or restart the service for changes to take effect

## Troubleshooting

### Build Fails

- Check the build logs in Railway dashboard
- Ensure `requirements.txt` is in the `backend` directory
- Verify Python version compatibility (check `runtime.txt`)

### Application Won't Start

- Check the deployment logs
- Verify all required environment variables are set
- Ensure the `Procfile` command is correct
- Check that the port is set to `$PORT` (Railway provides this)

### Database Connection Issues

- Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Check if your Supabase project allows connections from Railway's IPs
- Review Supabase connection settings

### CORS Errors

- Update `CORS_ORIGINS` to include your frontend domain
- Ensure the format is correct (JSON array string)

## How to Redeploy Your Backend

There are several ways to redeploy your backend on Railway:

### Method 1: Automatic Redeploy (Recommended)

Railway automatically redeploys when you push changes to your connected branch:

1. **Make your code changes** locally
2. **Commit your changes**:
   ```bash
   cd backend
   git add .
   git commit -m "Your commit message"
   git push
   ```
3. **Railway will automatically detect the push** and start a new deployment
4. **Monitor the deployment** in the Railway dashboard under the **Deployments** tab

### Method 2: Manual Redeploy from Dashboard

If you need to redeploy without code changes (e.g., after updating environment variables):

1. Go to your Railway project dashboard
2. Click on your service
3. Go to the **Deployments** tab
4. Find the deployment you want to redeploy (usually the latest one)
5. Click the **three dots (⋯)** menu on the right side of the deployment
6. Click **"Redeploy"**
7. Confirm the redeployment
8. Watch the build logs as it redeploys

### Method 3: Redeploy via Railway CLI

If you have Railway CLI installed:

1. **Install Railway CLI** (if not already installed):
   ```bash
   npm i -g @railway/cli
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Link your project** (if not already linked):
   ```bash
   cd backend
   railway link
   ```

4. **Redeploy**:
   ```bash
   railway up
   ```

### Method 4: Trigger Redeploy via API

You can also trigger a redeploy programmatically using Railway's API, but the dashboard method is usually easier.

### When to Redeploy

You should redeploy when:
- ✅ You've pushed new code changes
- ✅ You've updated environment variables
- ✅ You want to restart the application
- ✅ You've fixed a bug and want to apply the fix
- ✅ You've updated dependencies in `requirements.txt`

### After Redeploying

1. **Check the deployment logs** to ensure it completed successfully
2. **Test your endpoints**:
   - Health check: `https://your-app.up.railway.app/health`
   - API docs: `https://your-app.up.railway.app/api/docs`
3. **Monitor for any errors** in the logs

## Continuous Deployment

Railway automatically deploys when you push to your connected branch:
- Default branch (usually `main` or `master`) = Production
- You can set up preview deployments for other branches

## Monitoring

1. **Logs**: View real-time logs in the Railway dashboard
2. **Metrics**: Check CPU, memory, and network usage
3. **Alerts**: Set up alerts for deployment failures

## Cost Management

- Railway offers a free tier with $5 credit monthly
- Monitor usage in the dashboard
- Set spending limits if needed

## Additional Tips

1. **Database Migrations**: Run migrations manually via Railway's CLI or add a migration step to your deployment
2. **Health Checks**: Railway uses your `/health` endpoint for health checks
3. **Scaling**: Railway can auto-scale based on traffic
4. **Backups**: Consider setting up database backups if using Railway's database service

## Next Steps

After deployment:
1. Update your frontend to use the new Railway URL
2. Set up a custom domain (optional)
3. Configure monitoring and alerts
4. Set up CI/CD for automated deployments

