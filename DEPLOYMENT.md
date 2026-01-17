# Render Deployment Guide for PRISM

## 📋 Prerequisites
- GitHub account with your repository
- Render account (sign up at https://render.com)
- Your API keys ready:
  - `OPENROUTER_API_KEY`
  - `BIOPORTAL_API_KEY`

---

## 🚀 Step-by-Step Deployment

### Step 1: Connect GitHub to Render
1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Click **"Connect a repository"**
4. Select your GitHub account and authorize Render
5. Select the **"Escape-Da-Vinci"** repository
6. Click **"Connect"**

### Step 2: Configure Backend Service
1. **Name**: `prism-backend`
2. **Environment**: `Python 3`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `python -m uvicorn server.main:app --host 0.0.0.0 --port $PORT`
5. **Plan**: Free or paid (your choice)
6. **Region**: Choose closest to you (e.g., Oregon, Frankfurt)

### Step 3: Add Environment Variables to Backend
Click **"Advanced"** and add these environment variables:

```
OPENROUTER_API_KEY = your_actual_api_key_here
BIOPORTAL_API_KEY = your_actual_api_key_here
PYTHONUNBUFFERED = true
```

### Step 4: Deploy Backend
Click **"Create Web Service"** and wait for deployment (2-3 minutes)

You'll get a URL like: `https://prism-backend.onrender.com`

---

### Step 5: Deploy Frontend (Static Site)
1. Go back to dashboard, click **"New +"** → **"Static Site"**
2. Connect the same repository
3. **Name**: `prism-frontend`
4. **Build Command**: `cd frontend && npm install && npm run build`
5. **Publish Directory**: `frontend/dist`

### Step 6: Connect Frontend to Backend
After frontend deploys:
1. Go to frontend service settings
2. Click **"Environment"**
3. Add custom environment variable:
   ```
   VITE_API_URL = https://prism-backend.onrender.com
   ```
4. Redeploy frontend

---

## 🔗 After Deployment

Your services will be live at:
- **Backend API**: `https://prism-backend.onrender.com`
- **Frontend**: `https://prism-frontend.onrender.com`

The frontend automatically detects and uses the backend API.

---

## 📝 Troubleshooting

### Backend won't start
- Check that `OPENROUTER_API_KEY` is set correctly
- Check backend logs: Dashboard → Service → Logs

### Frontend shows API errors
- Make sure backend is running first
- Check network tab in browser DevTools
- Verify environment variables are set

### Cold start delays
- Render free tier has cold starts (⏱️ ~30 seconds)
- Upgrade to paid to prevent cold starts

### Deploy again
- Push new changes to GitHub
- Render auto-deploys on push
- Manual: Dashboard → Service → Manual Deploy

---

## ⚙️ Important Notes

✅ **Automatic deploys enabled** - Any push to main branch auto-deploys
✅ **Environment variables** - Set in Render dashboard, not in .env
✅ **Database** - Currently using in-memory storage; add PostgreSQL if needed
✅ **API timeout** - Set to 3 minutes to handle AI agent processing

---

## 🆘 Need Help?
- Check Render docs: https://render.com/docs
- Check service logs: Dashboard → Service → Logs tab
- Restart service: Dashboard → Service → More → Restart
