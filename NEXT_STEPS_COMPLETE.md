# ✅ Next Steps - Complete Implementation Guide

**Status**: API Gateways Created ✅ | Backend Deployment Required ⚠️

---

## 🎯 Quick Summary

**What's Done**:
- ✅ REST API Gateway created: `https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod`
- ✅ WebSocket API Gateway created: `wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod`
- ✅ Code changes ready (backend & frontend)

**What's Needed**:
1. Deploy backend code to EC2
2. Update Vercel environment variables
3. Test everything

---

## Step 1: Deploy Backend Code (15 minutes)

### Option A: Use PowerShell Script
```powershell
.\deploy_backend_api_gateway.ps1
```

### Option B: Manual SSH Deployment
```bash
# SSH into EC2
ssh -i ~/Downloads/pipeline_orchestrator.pem ec2-user@13.58.115.166

# Run these commands:
cd /opt/pipeline
sudo git pull
cd backend

# Update .env file
sudo nano .env
# Add/Update: FRONTEND_URL=https://pipeline-q3b1.vercel.app

# Restart service
sudo systemctl restart pipeline-backend
sudo systemctl status pipeline-backend
```

**Verification**:
```bash
# Test direct backend
curl http://13.58.115.166:8000/health

# Test via API Gateway (should work after deployment)
curl https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod/api/health
```

---

## Step 2: Update Vercel Environment Variables (5 minutes)

### Via Vercel Dashboard (Recommended)

1. Go to: **https://vercel.com/dashboard**
2. Select your project: **pipeline** (or your project name)
3. Navigate to: **Settings** → **Environment Variables**
4. Add/Update these variables:

   **Variable 1**:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod`
   - **Environment**: Select **Production** (and Preview/Development if needed)
   - Click **Save**

   **Variable 2**:
   - **Key**: `NEXT_PUBLIC_WS_URL`
   - **Value**: `wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod`
   - **Environment**: Select **Production** (and Preview/Development if needed)
   - Click **Save**

5. **Vercel will automatically redeploy** after environment variable changes

### Via Vercel CLI (Alternative)

```bash
cd frontend

# If not linked, link first
vercel link

# Add environment variables
vercel env add NEXT_PUBLIC_API_URL production
# When prompted, enter: https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod

vercel env add NEXT_PUBLIC_WS_URL production
# When prompted, enter: wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod

# Redeploy
vercel --prod
```

---

## Step 3: Test Everything (30 minutes)

### 3.1 Test REST API Gateway

```bash
# Test health endpoint
curl https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod/api/health

# Expected response:
# {"status":"healthy","timestamp":"..."}
```

**If you get 502/500**: Backend not deployed yet (expected)
**If you get 200**: ✅ Backend is working!

### 3.2 Test WebSocket API Gateway

**Browser Console Test** (on https://pipeline-q3b1.vercel.app/):

```javascript
const sessionId = 'test-session-123';
const wsUrl = `wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod?session_id=${sessionId}`;
const ws = new WebSocket(wsUrl);

ws.onopen = () => {
    console.log('✅ WebSocket connected via API Gateway');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('📨 Message received:', data);
};

ws.onerror = (error) => {
    console.error('❌ WebSocket error:', error);
};

ws.onclose = (event) => {
    console.log('🔌 WebSocket closed:', event.code, event.reason);
};
```

**Expected**: Connection opens and receives `{"type":"connection_ready",...}` message

### 3.3 Test Frontend Integration

1. Open: **https://pipeline-q3b1.vercel.app/**
2. Open browser **DevTools** → **Network** tab
3. Filter for **WS** (WebSocket) connections
4. Trigger a video generation or any action that uses WebSocket
5. Verify:
   - ✅ REST API calls go to: `https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod/api/...`
   - ✅ WebSocket connects to: `wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod?session_id=...`
   - ✅ No CORS errors in console
   - ✅ Agent status updates received via WebSocket

---

## 📊 Current Status

| Component | Status | URL/Details |
|-----------|--------|-------------|
| REST API Gateway | ✅ Created | `https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod` |
| WebSocket API Gateway | ✅ Created | `wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod` |
| Backend Code | ✅ Ready | Needs deployment to EC2 |
| Frontend Code | ✅ Ready | Auto-deploys with Vercel |
| Backend Deployment | ⚠️ Pending | Run Step 1 |
| Vercel Env Vars | ⚠️ Pending | Run Step 2 |
| Testing | ⚠️ Pending | Run Step 3 |

---

## 🔧 Troubleshooting

### Issue: REST API returns 502 Bad Gateway
**Cause**: Backend not deployed or service not running
**Fix**:
```bash
ssh ec2-user@13.58.115.166
sudo systemctl status pipeline-backend
sudo journalctl -u pipeline-backend -n 50
```

### Issue: WebSocket connection fails
**Cause**: Backend `/ws` endpoint not deployed
**Fix**: Ensure backend code is deployed (Step 1)

### Issue: CORS errors in browser
**Cause**: `FRONTEND_URL` not set in backend `.env`
**Fix**: Update `.env` file and restart service (Step 1)

### Issue: Frontend still uses old URLs
**Cause**: Vercel environment variables not updated
**Fix**: Complete Step 2, wait for Vercel redeploy

---

## ✅ Success Checklist

After completing all steps, verify:

- [ ] Backend service running on EC2
- [ ] REST API Gateway returns 200 OK for `/api/health`
- [ ] WebSocket connects via API Gateway
- [ ] Frontend makes API calls to API Gateway URL
- [ ] No CORS errors in browser console
- [ ] Agent status updates received via WebSocket
- [ ] Vercel environment variables updated

---

## 📝 Files Created

- `deploy_backend_api_gateway.ps1` - PowerShell deployment script
- `complete_next_steps.ps1` - Helper script with all instructions
- `backend/API_GATEWAY_URLS.md` - Complete URL reference
- `IMPLEMENTATION_COMPLETE.md` - Implementation summary

---

## 🚀 Ready to Complete

Run the 3 steps above to finish the implementation. Estimated time: **~50 minutes**

**Current API Gateway Status**: Created and ready, waiting for backend deployment.

