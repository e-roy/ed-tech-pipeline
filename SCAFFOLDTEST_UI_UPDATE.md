# Scaffoldtest UI - API Gateway Update

**Date**: 2025-01-19
**Status**: ✅ Updated for API Gateway Environment

---

## ✅ Changes Made

### 1. API Gateway Detection
- Added detection for API Gateway URLs (checks for `execute-api` in hostname)
- Automatically uses API Gateway URLs when accessed through API Gateway
- Falls back to direct connection for localhost/EC2 direct access

### 2. WebSocket Connection Updates
- **API Gateway**: Uses `wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod?session_id={session_id}` (query parameter)
- **Direct Connection**: Uses `ws://{host}/ws/{session_id}` (path parameter)
- Automatically detects which format to use based on access method

### 3. REST API Calls
- **API Gateway**: Uses `https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod` for all REST calls
- **Direct Connection**: Uses `window.location.origin` (same origin)

---

## 📍 Access Methods

### Option 1: Direct EC2 Access (HTTP)
**URL**: `http://13.58.115.166:8000/scaffoldtest`

**Behavior**:
- REST API: `http://13.58.115.166:8000/api/...`
- WebSocket: `ws://13.58.115.166:8000/ws/{session_id}`

### Option 2: API Gateway Access (HTTPS) ✅ Recommended
**URL**: `https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod/scaffoldtest`

**Behavior**:
- REST API: `https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod/api/...`
- WebSocket: `wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod?session_id={session_id}`

---

## 🔧 How It Works

The UI automatically detects the access method:

```javascript
// Detects API Gateway
const isApiGateway = window.location.hostname.includes('execute-api');

// Sets appropriate URLs
if (isApiGateway) {
    API_BASE_URL = REST_API_GATEWAY_URL;  // API Gateway REST
    wsUrl = WS_API_GATEWAY_URL;            // API Gateway WebSocket
    wsPath = `${wsUrl}?session_id=${sessionId}`;  // Query parameter
} else {
    API_BASE_URL = window.location.origin;  // Direct connection
    wsUrl = API_BASE_URL.replace('http://', 'ws://');
    wsPath = `${wsUrl}/ws/${sessionId}`;    // Path parameter
}
```

---

## ✅ Testing

### Test Direct Access
1. Open: `http://13.58.115.166:8000/scaffoldtest`
2. Check browser console - should show:
   ```
   API Base URL: http://13.58.115.166:8000
   Is API Gateway: false
   ```
3. Fill form and submit
4. Verify WebSocket connects to `ws://13.58.115.166:8000/ws/{session_id}`

### Test API Gateway Access
1. Open: `https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod/scaffoldtest`
2. Check browser console - should show:
   ```
   API Base URL: https://w8d3k51hg6.execute-api.us-east-2.amazonaws.com/prod
   Is API Gateway: true
   ```
3. Fill form and submit
4. Verify WebSocket connects to `wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod?session_id={session_id}`

---

## 📝 Notes

- The UI works in both environments automatically
- No manual configuration needed
- WebSocket format automatically adjusts (query vs path parameter)
- REST API calls automatically use correct base URL

---

## 🎯 Benefits

1. ✅ Works with HTTPS (API Gateway)
2. ✅ Works with HTTP (direct EC2)
3. ✅ Automatic detection - no manual config
4. ✅ WebSocket format automatically correct
5. ✅ No CORS issues (API Gateway handles it)

---

**Status**: ✅ Ready to use in both environments!

