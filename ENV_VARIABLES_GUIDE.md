# Environment Variables Guide

**Date**: 2025-01-19
**Status**: What to update in your .env files

---

## 📋 Summary

You need to update environment variables in **2 places**:

1. **Frontend `.env` file** (for local development)
2. **Vercel Dashboard** (for production deployment)

The backend `.env` on EC2 is already updated ✅

---

## 1. Frontend Local Development `.env` File

**Location**: `frontend/.env` or `frontend/.env.local`

**Add/Update these variables**:

```env
# Production ALB (HTTPS + WSS)
NEXT_PUBLIC_API_URL=https://api.gauntlet3.com
NEXT_PUBLIC_WS_URL=wss://api.gauntlet3.com

# For local development, you can use:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

**Note**: 
- `NEXT_PUBLIC_*` variables are exposed to the browser
- These are the API Gateway URLs we created
- For local dev, you can still use `http://localhost:8000` if running backend locally

---

## 2. Vercel Production Environment Variables

**Location**: Vercel Dashboard → Your Project → Settings → Environment Variables

**Add/Update these variables**:

| Variable Name | Value | Environment |
|---------------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://api.gauntlet3.com` | Production, Preview, Development |
| `NEXT_PUBLIC_WS_URL` | `wss://api.gauntlet3.com` | Production, Preview, Development |

**Steps**:
1. Go to: https://vercel.com/dashboard
2. Select your project
3. Click **Settings** → **Environment Variables**
4. Click **Add New**
5. Enter variable name and value
6. Select environments (Production, Preview, Development)
7. Click **Save**
8. Repeat for second variable
9. **Vercel will auto-redeploy** after saving

---

## 3. Backend EC2 `.env` File (Already Done ✅)

**Location**: `/opt/pipeline/backend/.env` (on EC2)

**Already updated**:
```env
FRONTEND_URL=https://pipeline-q3b1.vercel.app
```

**Status**: ✅ Already deployed and configured

---

## 📝 Complete Frontend `.env` Example

If you're creating a new `.env` file in `frontend/`, here's a complete example:

```env
# Database
DATABASE_URL="postgresql://user:password@localhost:5432/pipeline"

# NextAuth
AUTH_SECRET="your-secret-key-here"
AUTH_GOOGLE_ID="your-google-client-id"
AUTH_GOOGLE_SECRET="your-google-client-secret"
NEXTAUTH_URL="http://localhost:3000"

# Backend API (ALB URLs)
NEXT_PUBLIC_API_URL=https://api.gauntlet3.com
NEXT_PUBLIC_WS_URL=wss://api.gauntlet3.com

# Optional: AWS (if needed)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
S3_BUCKET_NAME=pipeline-backend-assets
AWS_REGION=us-east-1
```

---

## 🔍 How to Verify

### Check Frontend Local `.env`
```bash
cd frontend
cat .env | grep NEXT_PUBLIC
```

Should show:
```
NEXT_PUBLIC_API_URL=https://api.gauntlet3.com
NEXT_PUBLIC_WS_URL=wss://api.gauntlet3.com
```

### Check Vercel Environment Variables
1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Verify both variables are listed
3. Check that they're enabled for Production environment

---

## 🎯 Quick Reference

**ALB URLs**:
- REST API: `https://api.gauntlet3.com`
- WebSocket: `wss://api.gauntlet3.com`

**What to Update**:
1. ✅ Frontend `.env` file (local development)
2. ✅ Vercel Dashboard (production)

**What's Already Done**:
- ✅ Backend `.env` on EC2 (already deployed)

---

## ⚠️ Important Notes

1. **Local Development**: 
   - You can use `http://localhost:8000` for local backend testing
   - Or use API Gateway URLs to test production setup

2. **Production (Vercel)**:
   - **Must** use the ALB URLs (HTTPS/WSS required)
   - Direct EC2 IP won't work (HTTP, not HTTPS)

3. **WebSocket URL**:
   - Frontend now connects to `wss://api.gauntlet3.com/ws/{session}` and also sends a `register` message for compatibility.

---

## ✅ Checklist

- [ ] Create/update `frontend/.env` with API Gateway URLs
- [ ] Update Vercel environment variables
- [ ] Verify Vercel auto-redeployed
- [ ] Test frontend locally (if needed)
- [ ] Test production frontend on Vercel

---

**Next Action**: Update your frontend `.env` file and Vercel environment variables! 🚀

