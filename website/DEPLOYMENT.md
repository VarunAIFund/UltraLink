# Railway Deployment Guide for UltraLink

This guide will help you deploy both the Flask backend and Next.js frontend to Railway.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Push your code to GitHub
3. **Supabase Database**: Your PostgreSQL database should already be running on Supabase

## Project Structure

```
website/
├── backend/          # Flask API
│   ├── app.py
│   ├── requirements.txt
│   └── runtime.txt   # Specifies Python 3.12
├── frontend/         # Next.js app
└── .env             # Environment variables (DO NOT commit)
```

## Step 1: Prepare Your Repository

Ensure all files are committed:
```bash
cd /Users/varunsharma/Desktop/UltraLink
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

## Step 2: Deploy Flask Backend to Railway

### 2.1 Create Backend Service

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your `UltraLink` repository
4. Railway will detect your project

### 2.2 Configure Backend Service

1. **Set Root Directory:**
   - Go to **Settings** → **Service Settings**
   - Set **Root Directory** to: `website/backend`

2. **Set Start Command:**
   - Go to **Settings** → **Deploy**
   - Set **Start Command** to: `python app.py`

3. **Add Environment Variables:**
   - Go to **Variables** tab
   - Add these variables:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     SUPABASE_URL=your_supabase_project_url
     SUPABASE_DB_PASSWORD=your_supabase_db_password
     ```

4. **Note Your Backend URL:**
   - After deployment, go to **Settings** → **Networking**
   - Click **Generate Domain**
   - Copy the URL (e.g., `https://ultralink-backend-production.up.railway.app`)

## Step 3: Deploy Next.js Frontend to Railway

### 3.1 Create Frontend Service

1. In the same Railway project, click **"New Service"**
2. Select **"GitHub Repo"** again
3. Choose your `UltraLink` repository

### 3.2 Configure Frontend Service

1. **Set Root Directory:**
   - Go to **Settings** → **Service Settings**
   - Set **Root Directory** to: `website/frontend`

2. **Railway Auto-Detection:**
   - Railway will automatically detect Next.js and configure build settings
   - Build Command: `npm run build`
   - Start Command: `npm start`

3. **Add Environment Variables:**
   - Go to **Variables** tab
   - Add:
     ```
     NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
     ```
   - Replace with your actual backend URL from Step 2.4

4. **Generate Frontend Domain:**
   - Go to **Settings** → **Networking**
   - Click **Generate Domain**
   - This is your production URL!

## Step 4: Verify Deployment

1. **Test Backend:**
   ```bash
   curl https://your-backend-url.railway.app/health
   ```
   Should return: `{"status": "ok"}`

2. **Test Frontend:**
   - Visit your frontend URL
   - Try a search query
   - Check browser console for any errors

## Common Issues & Solutions

### Backend Not Starting
- Check logs in Railway dashboard
- Verify all environment variables are set
- Ensure `requirements.txt` has all dependencies
- **Python 3.13 Issue:** If you see `ImportError: undefined symbol: _PyInterpreterState_Get`, ensure `runtime.txt` exists in `/backend` with `python-3.12`

### Frontend Can't Connect to Backend
- Verify `NEXT_PUBLIC_API_URL` points to correct backend URL
- Check CORS is enabled in Flask (already done in `app.py`)
- Ensure backend domain is accessible

### Database Connection Issues
- Verify Supabase credentials in backend environment variables
- Check Supabase connection pooler URL format
- Ensure IP restrictions allow Railway servers

## Environment Variables Summary

### Backend (.env)
```bash
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_DB_PASSWORD=your_password
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
```

## Updating Your Deployment

Railway auto-deploys on every push to your main branch:
```bash
git add .
git commit -m "Update feature"
git push origin main
```

## Cost Estimation

- **Railway Free Plan:** $5 credit/month (usually enough for small apps)
- **Usage-based pricing** after free tier
- Monitor usage in Railway dashboard

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- UltraLink Issues: Create an issue in your GitHub repo

---

**Deployment Checklist:**
- [ ] Code pushed to GitHub
- [ ] Backend service created on Railway
- [ ] Backend environment variables set
- [ ] Backend domain generated
- [ ] Frontend service created on Railway
- [ ] Frontend environment variable (API_URL) set
- [ ] Frontend domain generated
- [ ] Tested search functionality
- [ ] Verified database connection

---

🎉 **Your app should now be live!**
