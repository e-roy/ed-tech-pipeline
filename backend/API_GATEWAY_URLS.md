# API Gateway URLs - Production Configuration

**Last Updated**: 2025-01-19
**Region**: us-east-2
**Environment**: Production

---

## REST API Gateway

- **API Name**: `pipeline-backend-api`
- **API ID**: `w8d3k51hg6`
- **Stage**: `prod`
- **Base URL**: `https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod`
- **Health Check**: `https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod/api/health`

### Example Endpoints

- Health: `https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod/api/health`
- Get Session: `https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod/api/get-video-session/{session_id}`
- Start Processing: `https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod/api/startprocessing`

---

## WebSocket API Gateway

- **API Name**: `pipeline-backend-websocket`
- **API ID**: `927uc04ep5`
- **Stage**: `prod`
- **Base URL**: `wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod`
- **Connection Format**: `wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod?session_id={session_id}`

### Connection Example

```javascript
const sessionId = 'your-session-id';
const wsUrl = `wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod?session_id=${sessionId}`;
const ws = new WebSocket(wsUrl);
```

---

## EC2 Backend

- **Instance ID**: `i-051a27d0f69e98ca2`
- **Current IP**: `13.58.115.166` ⚠️ **NOT Elastic IP** (may change on restart)
- **Private IP**: `172.31.40.134`
- **Region**: us-east-2
- **Direct HTTP**: `http://13.58.115.166:8000`
- **Direct WebSocket**: `ws://13.58.115.166:8000/ws/{session_id}` or `ws://13.58.115.166:8000/ws?session_id={session_id}`

**Note**: Elastic IP association failed due to permissions. Current IP is being used. If IP changes, API Gateway integration URLs will need to be updated.

---

## Frontend Configuration

### Vercel Environment Variables (TO BE UPDATED)

- `NEXT_PUBLIC_API_URL`: `https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod`
- `NEXT_PUBLIC_WS_URL`: `wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod`

**Note**: Frontend code automatically appends `?session_id={session_id}` when `NEXT_PUBLIC_WS_URL` contains `execute-api`.

---

## Backend Configuration

### Environment Variables (`/opt/pipeline/backend/.env` - TO BE UPDATED)

- `FRONTEND_URL`: `https://pipeline-q3b1.vercel.app`

---

## Testing Commands

### REST API

```bash
# Health check
curl https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod/api/health

# Get session (requires auth token)
curl https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod/api/get-video-session/{session_id} \
  -H "Authorization: Bearer <token>"
```

### WebSocket

```bash
# Using wscat (install: npm install -g wscat)
wscat -c "wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod?session_id=test-123"
```

---

## Notes

- All APIs are in **us-east-2** region
- Security group allows `0.0.0.0/0` on port 8000 (public integration)
- S3 bucket still in us-east-1 (migration deferred)
- Elastic IP association requires manual setup via AWS Console (permission issue)
