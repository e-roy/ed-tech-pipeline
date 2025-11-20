# API Gateway Setup Guide - Complete Implementation

This guide walks through the complete setup of AWS API Gateway for the Pipeline Backend, including REST and WebSocket APIs.

## Prerequisites

- AWS CLI configured with profile `default1`
- Access to AWS Console (us-east-2 region)
- EC2 instance running: `i-051a27d0f69e98ca2`
- Vercel deployment: `https://pipeline-q3b1.vercel.app/`

---

## Phase 0: Pre-Setup (CRITICAL - Do First)

### Step 0.1: Allocate Elastic IP

**Why**: Current IP `13.58.115.166` is not an Elastic IP and will change on restart, breaking API Gateway.

**Steps**:
1. AWS Console → EC2 → Network & Security → Elastic IPs
2. Click "Allocate Elastic IP address"
3. Select "Amazon's pool of IPv4 addresses"
4. Click "Allocate"
5. **Note the new Elastic IP** (e.g., `54.123.45.67`)
6. Select the Elastic IP → Actions → Associate Elastic IP address
7. Select instance: `i-051a27d0f69e98ca2`
8. Select private IP: `172.31.40.134`
9. Click "Associate"

**Verification**:
```bash
aws ec2 describe-instances \
  --instance-ids i-051a27d0f69e98ca2 \
  --profile default1 \
  --region us-east-2 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text
```

**Update**: Replace `<elastic-ip>` in all following steps with your new Elastic IP.

---

## Phase 1: Backend Code Updates

### Step 1.1: Verify Backend Code Changes

The backend code has been updated to support WebSocket query parameters:
- ✅ New endpoint: `/ws` (accepts `?session_id=xxx`)
- ✅ Existing endpoint: `/ws/{session_id}` (backward compatible)

**File**: `backend/app/main.py` (already updated)

### Step 1.2: Deploy Backend Changes

```bash
# SSH into EC2
ssh -i ~/Downloads/pipeline_orchestrator.pem ec2-user@<elastic-ip>

# Navigate to repo
cd /opt/pipeline
sudo git pull

# Restart service
sudo systemctl restart pipeline-backend

# Verify service is running
sudo systemctl status pipeline-backend

# Check logs
sudo journalctl -u pipeline-backend -f
```

**Verification**:
```bash
# Test health endpoint
curl http://<elastic-ip>:8000/health

# Test WebSocket endpoint (from local machine with wscat)
# Install wscat: npm install -g wscat
wscat -c ws://<elastic-ip>:8000/ws?session_id=test-123
```

---

## Phase 2: Create REST API Gateway

### Step 2.1: Create REST API

1. AWS Console → API Gateway → Create API
2. Select **REST API** → Build
3. Configure:
   - **Protocol**: REST
   - **Create new API**: New API
   - **API name**: `pipeline-backend-api`
   - **Description**: "Pipeline Backend REST API for HTTPS access"
   - **Endpoint Type**: Regional
4. Click "Create API"

### Step 2.2: Create Resources

1. In API Gateway console, select your API
2. Click "Actions" → "Create Resource"
3. Configure:
   - **Resource Name**: `api`
   - **Resource Path**: `/api`
   - ✅ Enable "Configure as proxy resource"
4. Click "Create Resource"

### Step 2.3: Create Method

1. Select `/api` resource
2. Click "Actions" → "Create Method"
3. Select **ANY** from dropdown
4. Click checkmark
5. Configure Integration:
   - **Integration type**: HTTP
   - **Endpoint URL**: `http://<elastic-ip>:8000/{proxy}`
   - ✅ Enable "Use HTTP Proxy Integration"
   - **HTTP Method**: ANY
   - **Content Handling**: Passthrough
6. Click "Save"

### Step 2.4: Deploy API

1. Click "Actions" → "Deploy API"
2. Configure:
   - **Deployment stage**: `[New Stage]`
   - **Stage name**: `prod`
   - **Stage description**: "Production stage"
3. Click "Deploy"
4. **Note the Invoke URL** (e.g., `https://abc123.execute-api.us-east-2.amazonaws.com/prod`)

**Document the REST API URL**: `https://<api-id>.execute-api.us-east-2.amazonaws.com/prod`

---

## Phase 3: Create WebSocket API Gateway

### Step 3.1: Create WebSocket API

1. AWS Console → API Gateway → Create API
2. Select **WebSocket API** → Build
3. Configure:
   - **API name**: `pipeline-backend-websocket`
   - **Route Selection Expression**: `$request.body.action` (or `$default`)
   - **Description**: "Pipeline Backend WebSocket API for real-time updates"
4. Click "Create API"

### Step 3.2: Create $connect Route

1. In WebSocket API console, click "Routes" → "Create"
2. Configure:
   - **Route key**: `$connect`
   - **Route type**: `$connect`
3. Click "Next"
4. Configure Integration:
   - **Integration type**: HTTP
   - **Integration URL**: `http://<elastic-ip>:8000/ws?session_id=$request.querystring.session_id`
   - **Note**: API Gateway will extract `session_id` from query string and pass it to backend
5. Click "Create"

### Step 3.3: Create $disconnect Route

1. Click "Routes" → "Create"
2. Configure:
   - **Route key**: `$disconnect`
   - **Route type**: `$disconnect`
3. Click "Next"
4. Configure Integration:
   - **Integration type**: HTTP
   - **Integration URL**: `http://<elastic-ip>:8000/ws?session_id=$request.querystring.session_id`
5. Click "Create"

### Step 3.4: Create $default Route

1. Click "Routes" → "Create"
2. Configure:
   - **Route key**: `$default`
   - **Route type**: `$default`
3. Click "Next"
4. Configure Integration:
   - **Integration type**: HTTP
   - **Integration URL**: `http://<elastic-ip>:8000/ws?session_id=$request.querystring.session_id`
5. Click "Create"

### Step 3.5: Deploy WebSocket API

1. Click "Stages" → "Create"
2. Configure:
   - **Stage name**: `prod`
   - **Description**: "Production stage"
3. Click "Create"
4. **Note the WebSocket URL** (e.g., `wss://abc123.execute-api.us-east-2.amazonaws.com/prod`)

**Document the WebSocket API URL**: `wss://<api-id>.execute-api.us-east-2.amazonaws.com/prod`

---

## Phase 4: Update Configuration

### Step 4.1: Update Backend CORS

**File**: `/opt/pipeline/backend/.env` (on EC2)

Add/Update:
```bash
FRONTEND_URL=https://pipeline-q3b1.vercel.app
```

**File**: `backend/app/main.py` (verify CORS configuration includes Vercel URL)

Restart backend:
```bash
sudo systemctl restart pipeline-backend
```

### Step 4.2: Update Vercel Environment Variables

1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Update/Add:
   - `NEXT_PUBLIC_API_URL`: `https://<rest-api-id>.execute-api.us-east-2.amazonaws.com/prod`
   - `NEXT_PUBLIC_WS_URL`: `wss://<websocket-api-id>.execute-api.us-east-2.amazonaws.com/prod`
3. **Important**: For WebSocket URL, frontend code should append `?session_id={session_id}` when connecting
4. Redeploy frontend (or wait for automatic deployment)

---

## Phase 5: Testing & Verification

### Step 5.1: Test REST API Gateway

```bash
# Test health endpoint
curl https://<rest-api-id>.execute-api.us-east-2.amazonaws.com/prod/api/health

# Expected: {"status":"healthy",...}

# Test session endpoint (replace with actual session_id)
curl https://<rest-api-id>.execute-api.us-east-2.amazonaws.com/prod/api/get-video-session/<session_id> \
  -H "Authorization: Bearer <token>"
```

### Step 5.2: Test WebSocket API Gateway

**Browser Console Test**:
```javascript
const sessionId = 'test-session-123';
const wsUrl = `wss://<websocket-api-id>.execute-api.us-east-2.amazonaws.com/prod?session_id=${sessionId}`;
const ws = new WebSocket(wsUrl);

ws.onopen = () => {
  console.log('✅ WebSocket connected via API Gateway');
};

ws.onmessage = (event) => {
  console.log('📨 Message:', JSON.parse(event.data));
};

ws.onerror = (error) => {
  console.error('❌ WebSocket error:', error);
};

ws.onclose = (event) => {
  console.log('🔌 WebSocket closed:', event.code, event.reason);
};
```

### Step 5.3: Test Frontend Integration

1. Open `https://pipeline-q3b1.vercel.app/`
2. Open browser DevTools → Network tab
3. Filter for "WS" (WebSocket) connections
4. Trigger a video generation
5. Verify:
   - ✅ REST API calls go to API Gateway URL
   - ✅ WebSocket connects to API Gateway URL
   - ✅ Agent status updates are received

---

## Phase 6: Documentation

### Step 6.1: Document API Gateway URLs

Create/Update `backend/API_GATEWAY_URLS.md`:

```markdown
# API Gateway URLs

## REST API Gateway
- **URL**: `https://<api-id>.execute-api.us-east-2.amazonaws.com/prod`
- **Health Check**: `https://<api-id>.execute-api.us-east-2.amazonaws.com/prod/api/health`
- **Created**: <date>
- **Region**: us-east-2

## WebSocket API Gateway
- **URL**: `wss://<api-id>.execute-api.us-east-2.amazonaws.com/prod`
- **Connection Format**: `wss://<api-id>.execute-api.us-east-2.amazonaws.com/prod?session_id={session_id}`
- **Created**: <date>
- **Region**: us-east-2

## EC2 Backend
- **Elastic IP**: `<elastic-ip>`
- **Instance ID**: `i-051a27d0f69e98ca2`
- **Region**: us-east-2
```

### Step 6.2: Update API.md

Update `backend/API.md` with API Gateway URLs and connection examples.

---

## Troubleshooting

### Issue: REST API returns 502 Bad Gateway

**Causes**:
- EC2 instance not running
- Security group blocking port 8000
- Backend service not running

**Fix**:
```bash
# Check EC2 status
aws ec2 describe-instances --instance-ids i-051a27d0f69e98ca2 --profile default1 --region us-east-2

# Check backend service
ssh ec2-user@<elastic-ip>
sudo systemctl status pipeline-backend
sudo journalctl -u pipeline-backend -n 50
```

### Issue: WebSocket connection fails

**Causes**:
- Query parameter not passed correctly
- Backend WebSocket endpoint not accepting query params
- CORS issues

**Fix**:
1. Verify backend code has `/ws` endpoint
2. Check API Gateway integration URL includes query parameter
3. Test direct connection: `wscat -c ws://<elastic-ip>:8000/ws?session_id=test`

### Issue: CORS errors in browser

**Causes**:
- Frontend URL not in CORS allowlist
- API Gateway domain not allowed

**Fix**:
1. Update `FRONTEND_URL` in backend `.env`
2. Restart backend service
3. Check CORS middleware configuration

---

## Rollback Plan

If issues occur:

1. **Revert Vercel Environment Variables**:
   - Change `NEXT_PUBLIC_API_URL` back to `http://<elastic-ip>:8000`
   - Change `NEXT_PUBLIC_WS_URL` back to `ws://<elastic-ip>:8000/ws?session_id={session_id}`

2. **Delete API Gateways** (if needed):
   - AWS Console → API Gateway → Select API → Actions → Delete

3. **Backend continues running** - no data loss

---

## Success Criteria Checklist

- [ ] Elastic IP allocated and associated
- [ ] Backend code deployed with WebSocket query param support
- [ ] REST API Gateway created and deployed
- [ ] WebSocket API Gateway created and deployed
- [ ] Vercel environment variables updated
- [ ] Backend CORS updated with Vercel URL
- [ ] REST API endpoints accessible via HTTPS
- [ ] WebSocket connections work via WSS
- [ ] Frontend can make API calls from Vercel
- [ ] Agent status updates received via WebSocket
- [ ] All documentation updated

---

## Next Steps After Setup

1. **Monitor API Gateway Metrics**:
   - CloudWatch → API Gateway → Metrics
   - Set up alarms for errors and latency

2. **Cost Monitoring**:
   - Set up billing alerts
   - Monitor API Gateway usage

3. **Security Hardening** (Optional):
   - Add API keys for REST API
   - Implement WebSocket authorizer
   - Set up rate limiting

4. **S3 Migration** (Future):
   - Plan migration of 3.39 GB from us-east-1 to us-east-2
   - Update code to use us-east-2 bucket

---

## Notes

- **Elastic IP Cost**: Free when associated with running instance
- **API Gateway Cost**: ~$5-20/month for low-medium traffic
- **Security**: Currently using public integration (0.0.0.0/0) - acceptable for MVP
- **S3 Migration**: Can be deferred - current bucket works from any region

