# HTTPS Implementation Plan: AWS API Gateway for Pipeline Backend

## Problem Statement

### Current Issues

1. **Vercel HTTPS Requirement**
   - Vercel frontend (deployed at `https://*.vercel.app`) cannot make HTTP requests to backend APIs
   - Browser security policies block mixed content (HTTPS page calling HTTP API)
   - Current backend at `http://<ec2-ip>:8000` is inaccessible from Vercel

2. **PostgreSQL SSL Connection Issues**
   - Neon PostgreSQL requires SSL connections (`sslmode=require`)
   - Current connection attempts fail with certificate file permission errors
   - Error: `could not open certificate file "/home/ec2-user/.postgresql/postgresql.crt": Permission denied`

3. **Security Concerns**
   - No encryption for API traffic
   - Credentials and sensitive data transmitted in plaintext
   - Not production-ready

### Impact

- Frontend cannot communicate with backend API
- Database connections fail intermittently
- Security vulnerabilities in production
- Blocks deployment of full-stack application

---

## Solution Architecture

### Approach: AWS API Gateway (REST + WebSocket) + HTTP Integration

**Why This Solution Works:**

1. **AWS-Native**: Fully integrated with AWS ecosystem
2. **Managed HTTPS**: Automatic SSL/TLS termination, no certificate management
3. **Quick Returns**: API Gateway works perfectly with our architecture where endpoints return immediately and use WebSocket for long-running operations
4. **WebSocket Support**: Separate WebSocket API Gateway handles real-time agent progress updates
5. **Cost Effective**: Pay-per-request pricing, no base cost for low traffic
6. **Production Ready**: Built-in DDoS protection, monitoring, and scaling

### Architecture Diagram

```
Internet (HTTPS)
    ↓
API Gateway REST API (HTTPS) - SSL Termination
    ↓
EC2 Backend (HTTP, Port 8000) - Internal
    ↓
Neon PostgreSQL (SSL with sslmode=prefer)
```

**WebSocket Flow:**
```
Client (WSS)
    ↓
API Gateway WebSocket API (WSS) - SSL Termination
    ↓
EC2 Backend WebSocket (WS, Port 8000) - Internal
```

### Key Components

1. **REST API Gateway**: Handles all HTTP endpoints (`/api/*`)
2. **WebSocket API Gateway**: Handles WebSocket connections (`/ws/*`)
3. **HTTP Integration**: Both APIs forward to EC2 backend (no Lambda)
4. **Database Fix**: Change `sslmode=require` to `sslmode=prefer` to avoid certificate file lookups

---

## WebSocket Complexity Explained

### Why Two Separate APIs?

API Gateway has two distinct API types:

1. **REST API Gateway**: For HTTP/HTTPS requests
   - Handles: `GET /api/health`, `POST /api/startprocessing`, etc.
   - Returns immediately (perfect for our quick-return endpoints)
   - 29-second timeout limit (not an issue since we return immediately)

2. **WebSocket API Gateway**: For WebSocket connections
   - Handles: `wss://api-gateway-url/ws/{session_id}`
   - Long-lived connections for real-time updates
   - No timeout limit
   - Uses connection IDs and route selection expressions

### Why This Works for Our Architecture

Our current implementation is already optimized for this:

1. **Quick Returns**: `/api/startprocessing` returns immediately (lines 448-452 in `main.py`)
   - Starts background tasks asynchronously
   - Returns success response within seconds
   - Well under API Gateway's 29-second limit

2. **WebSocket for Progress**: All long-running operations use WebSocket
   - Agent status updates sent via WebSocket
   - No long-running HTTP requests
   - Perfect for WebSocket API Gateway

3. **Separation of Concerns**:
   - HTTP endpoints: Quick operations, data retrieval, status checks
   - WebSocket: Real-time progress, agent updates, long-running operations

---

## Current Infrastructure Status (Verified via AWS)

### EC2 Instance Details
- **Instance ID**: `i-051a27d0f69e98ca2`
- **Current IP**: `13.58.115.166` (⚠️ **NOT an Elastic IP** - will change on restart)
- **Region**: `us-east-2` (not us-east-2)
- **Instance Type**: `t3.micro`
- **Private IP**: `172.31.40.134`
- **Security Group**: `launch-wizard-9` (sg-008d6dd819c207292)
  - Port 22: `0.0.0.0/0` ✅ Already configured
  - Port 8000: `0.0.0.0/0` ✅ Already configured for API Gateway

### S3 Bucket Details
- **Bucket Name**: `pipeline-backend-assets`
- **Current Region**: `us-east-2` ⚠️ **Needs migration to us-east-2**
- **Data Size**: 3.39 GB (3,468 MB)
- **Object Count**: 1,799 objects
- **Migration Priority**: **HIGH** (large amount of data)

### API Gateway Resources
- **Existing REST APIs in us-east-2**: 18 (unrelated projects - can ignore)
- **Existing WebSocket APIs**: Unknown (check console manually)
- **VPC Endpoints**: None found (will use public integration)

### Frontend Details
- **Vercel URL**: `https://pipeline-q3b1.vercel.app/`
- **CORS Configuration**: Needs update to allow this domain

---

## Implementation Steps

### Phase 0: Pre-Implementation Checklist

#### 0.1 Allocate Elastic IP (CRITICAL - Do First)
**Why**: Current IP `13.58.115.166` is not an Elastic IP and will change on instance restart, breaking API Gateway integration.

**Steps**:
1. AWS Console → EC2 → Network & Security → Elastic IPs
2. Click "Allocate Elastic IP address"
3. Select "Amazon's pool of IPv4 addresses"
4. Click "Allocate"
5. Select the newly allocated Elastic IP
6. Click "Actions" → "Associate Elastic IP address"
7. Select instance: `i-051a27d0f69e98ca2`
8. Click "Associate"
9. **Note the new Elastic IP** (will replace `13.58.115.166`)

**Verification**:
```bash
# Check instance now has Elastic IP
aws ec2 describe-instances --instance-ids i-051a27d0f69e98ca2 --profile default1 --region us-east-2
```

**Update**: Replace all references to `13.58.115.166` with the new Elastic IP in:
- API Gateway integration URLs
- Documentation
- Scripts

#### 0.2 S3 Bucket Migration (Optional - Can Do Later)
**Status**: 3.39 GB of data needs migration from us-east-2 to us-east-2

**Options**:
- **Option A**: Migrate now (recommended for clean setup)
  - Use `aws s3 sync` or S3 Cross-Region Replication
  - Estimated time: 1-2 hours for 3.39 GB
- **Option B**: Create new bucket in us-east-2, migrate gradually
- **Option C**: Keep old bucket, create new one (not recommended - breaks existing URLs)

**Recommendation**: For MVP, we can keep using us-east-2 bucket temporarily, but update code to use us-east-2 for new uploads. Full migration can happen later.

### Phase 1: Database SSL Fix (Already Completed)

**File**: `backend/app/database.py`

- Changed `sslmode=require` to `sslmode=prefer` in connection configuration
- This allows SSL when available but doesn't require certificate files
- Prevents permission errors on EC2 instance

**Status**: Code change completed, needs deployment

### Phase 2: Create REST API Gateway

**Steps:**

1. **Create REST API**:
   - AWS Console → API Gateway → Create API → REST API
   - Name: `pipeline-backend-api`
   - Description: "Pipeline Backend REST API"
   - Endpoint Type: Regional

2. **Create Resources**:
   - Create resource: `/api`
   - Create resource: `/api/{proxy+}` (catch-all for all `/api/*` paths)

3. **Create Method**:
   - Method: `ANY` (handles GET, POST, PUT, DELETE, etc.)
   - Integration Type: HTTP
   - Integration URL: `http://<ec2-ip>:8000/{proxy}`
   - Enable "Use HTTP Proxy Integration"

4. **Configure Integration**:
   - HTTP Method: `ANY`
   - Content Handling: Passthrough
   - Timeout: 29 seconds (maximum)

5. **Deploy API**:
   - Create stage: `prod`
   - Deploy to stage
   - Note the Invoke URL (e.g., `https://abc123.execute-api.us-east-2.amazonaws.com/prod`)

### Phase 3: Create WebSocket API Gateway

**Steps:**

1. **Create WebSocket API**:
   - AWS Console → API Gateway → Create API → WebSocket API
   - Name: `pipeline-backend-websocket`
   - Route Selection Expression: `$request.body.action` (or `$default`)

2. **Create Routes**:
   - Route: `$connect` - Connection initiation
   - Route: `$disconnect` - Connection termination
   - Route: `$default` - Default route for all messages

3. **Configure Integration**:
   - Integration Type: HTTP Proxy
   - **Integration URL**: `http://<elastic-ip>:8000/ws?session_id={session_id}`
   - **Note**: Using query parameter for `session_id` (easiest implementation)
   - For `$connect`: Forward connection to backend with `session_id` in query string
   - For `$default`: Forward messages to backend
   - **Route Selection Expression**: `$request.body.action` or `$default`
   
   **WebSocket Session ID Routing**:
   - **Easiest Approach**: Use query parameter `?session_id=xxx`
   - Client connects: `wss://gateway-url/prod?session_id=abc123`
   - API Gateway extracts `session_id` from query string
   - Backend receives: `ws://elastic-ip:8000/ws?session_id=abc123`
   - Backend code needs to extract from query params instead of path

4. **Deploy API**:
   - Create stage: `prod`
   - Deploy to stage
   - Note the WebSocket URL (e.g., `wss://abc123.execute-api.us-east-2.amazonaws.com/prod`)

### Phase 4: Update Security Groups

**EC2 Security Group:**

1. Allow inbound from API Gateway:
   - Type: Custom TCP
   - Port: 8000
   - Source: VPC CIDR (or API Gateway VPC endpoint if using private integration)

2. **Note**: For public HTTP integration, API Gateway uses public IPs. Consider:
   - Option A: Allow from `0.0.0.0/0` on port 8000 (simpler, but less secure)
   - Option B: Use VPC endpoint for private integration (more secure, more complex)

### Phase 5: Update Configuration

**Backend Environment Variables** (`/opt/pipeline/backend/.env`):
- No changes needed (backend still runs on port 8000 internally)
- CORS may need adjustment if API Gateway domain differs

**Frontend Environment Variables** (Vercel Dashboard):
- Update `NEXT_PUBLIC_API_URL` from `http://13.58.115.166:8000` to REST API Gateway URL
  - Example: `https://abc123.execute-api.us-east-2.amazonaws.com/prod`
- Update `NEXT_PUBLIC_WS_URL` from `ws://13.58.115.166:8000` to WebSocket API Gateway URL
  - Example: `wss://def456.execute-api.us-east-2.amazonaws.com/prod?session_id={session_id}`
  - **Note**: Include `?session_id=` in the base URL template

**CORS Configuration** (`backend/app/main.py`):
- Update `FRONTEND_URL` in `.env` to: `https://pipeline-q3b1.vercel.app`
- Ensure CORS allows requests from:
  - `https://pipeline-q3b1.vercel.app`
  - API Gateway domain (if needed)

### Phase 6: Testing & Verification

**REST API Endpoints:**
```bash
curl https://<rest-api-gateway-url>/api/health
curl https://<rest-api-gateway-url>/api/get-video-session/<session_id>
```

**WebSocket Connection:**
- Test from browser console or scaffoldtest UI
- Verify `wss://<websocket-api-gateway-url>/prod?session_id=<session_id>` connects
- Verify agent status updates are received
- **Test Script**:
  ```javascript
  const sessionId = 'test-session-123';
  const ws = new WebSocket(`wss://<websocket-api-gateway-url>/prod?session_id=${sessionId}`);
  ws.onopen = () => console.log('Connected');
  ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
  ```

**Database Connection:**
- Verify `/api/get-video-session/{session_id}` works
- Check logs for SSL connection success

---

## Why This Solution Works

### Technical Rationale

1. **Quick Return Pattern**
   - All HTTP endpoints return immediately (< 29 seconds)
   - Long-running operations use WebSocket for progress
   - Perfect fit for API Gateway's timeout limits

2. **WebSocket Separation**
   - REST API Gateway handles HTTP requests
   - WebSocket API Gateway handles real-time connections
   - Both point to same EC2 backend
   - Clean separation of concerns

3. **Managed SSL/TLS**
   - AWS handles certificate management
   - Automatic renewal
   - No certificate file management needed

4. **Database SSL Fix**
   - `sslmode=prefer` uses SSL when available without requiring certificate files
   - Neon PostgreSQL supports SSL without client certificates
   - Eliminates permission errors on EC2

### Cost Analysis

| Component | Cost |
|-----------|------|
| REST API Gateway | $3.50 per million requests |
| WebSocket API Gateway | $1.00 per million messages + $0.25 per million connection minutes |
| Data Transfer | Standard AWS data transfer rates |
| **Estimated Monthly** | **~$5-20 for low-medium traffic** |

**Comparison:**
- ALB: ~$16/month base + data transfer
- Nginx + Let's Encrypt: $0/month (but requires domain and maintenance)

### Risk Mitigation

1. **API Gateway Timeout**: Mitigated by:
   - All endpoints return immediately
   - Long operations use WebSocket
   - Background tasks handle processing

2. **WebSocket Connection Management**: Mitigated by:
   - Proper route configuration
   - Connection ID tracking
   - Error handling in WebSocket manager

3. **Cost Overruns**: Mitigated by:
   - CloudWatch alarms for request volume
   - Usage monitoring
   - Cost alerts configured

---

## API Endpoint Optimization

### Current Quick-Return Endpoints (No Changes Needed)

These endpoints already return quickly and work with API Gateway:

- `GET /api/health` - Health check (< 1 second)
- `GET /api/get-video-session/{session_id}` - Database query (< 2 seconds)
- `POST /api/startprocessing` - Returns immediately, uses background tasks
- `GET /api/monitor/sessions` - Session listing (< 2 seconds)

### WebSocket Endpoints (Minor Change Needed)

- `WS /ws/{session_id}` - Real-time agent progress updates
- **Update Required**: Support query parameter `?session_id=xxx` for API Gateway compatibility
- Code change: Extract `session_id` from query params if path param is missing
- Backward compatible: Still supports path parameter for direct connections

### Endpoints to Review (If Any Long-Running HTTP)

If any HTTP endpoints take > 29 seconds, they need to be refactored:

1. **Option A**: Return immediately, use WebSocket for progress
2. **Option B**: Split into multiple quick calls
3. **Option C**: Use async processing pattern (already implemented for `/api/startprocessing`)

---

## Rollback Plan

If issues occur:

1. **Revert Frontend Environment Variables**:
   - Change `NEXT_PUBLIC_API_URL` back to `http://<elastic-ip>:8000`
   - Change `NEXT_PUBLIC_WS_URL` back to `ws://<elastic-ip>:8000/ws?session_id={session_id}`
   - **Note**: Use Elastic IP (not the old dynamic IP)

2. **Delete API Gateway APIs** (if needed):
   - AWS Console → API Gateway → Delete API
   - No data loss, backend continues running

3. **Database Connection**: Already fixed in code, no rollback needed

---

## Success Criteria

- [ ] REST API Gateway accessible: `https://<rest-api-url>/api/health` returns 200 OK
- [ ] WebSocket API Gateway connects: `wss://<websocket-url>/prod?session_id=<session_id>` establishes connection
- [ ] Frontend can make API calls from Vercel
- [ ] WebSocket connections work over WSS
- [ ] Agent status updates received via WebSocket
- [ ] Database connections succeed without certificate errors
- [ ] All existing API endpoints functional
- [ ] Response times < 29 seconds for all HTTP endpoints

---

## Timeline Estimate

- **Elastic IP allocation**: 15 minutes
- **REST API Gateway setup**: 1 hour
- **WebSocket API Gateway setup**: 1 hour (includes query param routing)
- **Security group configuration**: ✅ Already done (0.0.0.0/0 on port 8000)
- **Backend WebSocket code update**: 30 minutes (extract session_id from query params)
- **Configuration updates**: 30 minutes
- **Testing**: 1 hour
- **Total**: ~4.5 hours

---

## Files Modified

1. `backend/app/database.py` - SSL mode change (already done)
2. `backend/app/main.py` - WebSocket endpoint: Support `session_id` from query params (for API Gateway compatibility)
   - Current: `/ws/{session_id}` (path parameter)
   - New: `/ws?session_id=xxx` (query parameter)
   - **Implementation**: Update endpoint to check query params first, fallback to path for backward compatibility
3. Vercel: Environment variables - Frontend API URLs
4. AWS: Elastic IP allocation and association (see `backend/ELASTIC_IP_CHECKLIST.md`)
5. AWS: API Gateway configurations (via console or CloudFormation)
6. EC2: Security group rules (✅ already configured)

---

## Next Steps After Implementation

1. **Monitoring**: Set up CloudWatch dashboards for API Gateway metrics
2. **Documentation**: Update API.md with API Gateway URLs
3. **Cost Optimization**: Review usage patterns, consider caching
4. **Security**: Review and harden API Gateway security settings
5. **Scaling**: Monitor performance, adjust as needed

---

## Additional Considerations

### Custom Domain (Optional)

API Gateway supports custom domains:

1. Request certificate in AWS Certificate Manager (ACM)
2. Create custom domain in API Gateway
3. Update DNS records
4. Use custom domain instead of `execute-api` URLs

**Benefits:**
- Professional URLs (e.g., `api.yourdomain.com`)
- Better branding
- Easier to remember

**Cost:** Free (certificate + domain registration)

### Caching (Optional)

API Gateway supports response caching:

- Cache GET requests for faster responses
- Reduce backend load
- Lower costs

**Consider caching:**
- `GET /api/health` (short TTL)
- `GET /api/monitor/sessions` (if data doesn't change frequently)

### Rate Limiting

API Gateway supports throttling:

- Configure default rate limits
- Protect backend from abuse
- Control costs

---

## Questions & Answers

**Q: Why not use Lambda instead of HTTP integration?**  
A: Our backend is already running on EC2 with WebSocket support. HTTP integration is simpler and maintains our current architecture.

**Q: Can we use one API Gateway for both REST and WebSocket?**  
A: No, they are separate API types. However, both can point to the same EC2 backend.

**Q: What about the 29-second timeout?**  
A: Not an issue. All our HTTP endpoints return quickly. Long operations use WebSocket.

**Q: How do we handle WebSocket authentication?**  
A: WebSocket API Gateway supports custom authorizers. Can use JWT tokens or API keys.

**Q: What if we need to scale beyond API Gateway limits?**  
A: API Gateway scales automatically. For very high traffic, consider ALB or CloudFront in front.

---

## References

- [AWS API Gateway REST API Documentation](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-rest-api.html)
- [AWS API Gateway WebSocket API Documentation](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api.html)
- [API Gateway Pricing](https://aws.amazon.com/api-gateway/pricing/)

