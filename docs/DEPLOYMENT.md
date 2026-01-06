# Deployment Guide - Render

This guide will help you deploy the OpenHammer API to Render's free tier.

## Prerequisites

1. GitHub account
2. Render account (sign up at https://render.com)
3. Your code pushed to a GitHub repository

## Step 1: Push to GitHub

If you haven't already, push your code to GitHub:

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit - OpenHammer API"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/openhammer-api.git
git branch -M main
git push -u origin main
```

**Important**: Make sure `data/json/` folder is included in your commit (the JSON files are needed for deployment).

## Step 2: Deploy to Render

### Option A: Using render.yaml (Automatic)

1. Go to https://render.com/dashboard
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` and configure everything
5. Click **"Apply"** to start deployment

### Option B: Manual Setup

1. Go to https://render.com/dashboard
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `openhammer-api` (or your choice)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
5. Click **"Create Web Service"**

## Step 3: Wait for Deployment

- Render will build and deploy your app (~2-3 minutes)
- You'll get a URL like: `https://openhammer-api.onrender.com`
- Visit `https://your-app.onrender.com/docs` to see your API docs

## Step 4: Test Your Deployment

Once deployed, test your API:

```bash
# Replace with your actual Render URL
curl https://openhammer-api.onrender.com/stats

curl https://openhammer-api.onrender.com/units?limit=5

curl https://openhammer-api.onrender.com/factions
```

## API Features Enabled

Your deployed API includes:

✅ **Rate Limiting**: 100 requests per minute per IP
✅ **HTTP Caching**: 1-hour cache for all responses
✅ **CORS**: Enabled for all origins
✅ **Auto-generated Docs**: Available at `/docs`

## Free Tier Limitations

Render's free tier has some limitations:

- **Spins down after 15 minutes of inactivity**
  - First request after inactivity takes ~30 seconds (cold start)
  - Subsequent requests are fast (<10ms)

- **750 hours/month** of runtime
  - More than enough for a side project
  - Resets monthly

- **No custom domain** on free tier
  - Use `yourapp.onrender.com` URL
  - Or upgrade to paid plan for custom domain

## Monitoring & Logs

- **View logs**: Render Dashboard → Your Service → "Logs" tab
- **Monitor usage**: Render Dashboard → Your Service → "Metrics" tab
- **Auto-deploys**: Pushes to `main` branch trigger automatic redeployment

## Upgrading to Paid Tier

If your API becomes popular, consider upgrading:

- **Starter Plan**: $7/month
  - No spin-down (always-on)
  - Better performance
  - 100GB bandwidth/month

## Troubleshooting

### Build fails
- Check that `requirements.txt` is in the root directory
- Verify Python version compatibility

### App crashes on startup
- Check logs in Render dashboard
- Verify `data/json/` folder is included in repository

### Slow first request
- Normal on free tier (cold start)
- Upgrade to paid tier for always-on service

## Next Steps

After deployment, you might want to:

1. **Share your API**: Give people your Render URL
2. **Add API documentation**: Link to `/docs` in your README
3. **Monitor usage**: Check Render metrics regularly
4. **Set up custom domain** (requires paid plan)

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- FastAPI Docs: https://fastapi.tiangolo.com

---

## Your API is Live! 🎉

Share your API URL with the community:
- `https://your-app.onrender.com/docs` - Interactive documentation
- `https://your-app.onrender.com/stats` - API statistics
- `https://your-app.onrender.com/units` - Unit data
