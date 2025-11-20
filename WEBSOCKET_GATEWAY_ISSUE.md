# WebSocket API Gateway Connection Issue

**Date**: 2025-01-20
**Status**: ⚠️ Connection Failing

---

## Problem

WebSocket connection through API Gateway is failing:
- URL: `wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod?session_id=xxx`
- Error: Connection fails with status 0 (connection not established)
- Browser shows: "WebSocket connection failed"

---

## What We Know

### ✅ Backend WebSocket Works
- Direct connection: `ws://13.58.115.166:8000/ws?session_id=test` ✅ Works
- Path parameter: `ws://13.58.115.166:8000/ws/test` ✅ Works
- Both endpoints return `connection_ready` message

### ⚠️ API Gateway Configuration
- Integration URI: `http://13.58.115.166:8000/ws?session_id=$request.querystring.session_id`
- Integration Type: `HTTP_PROXY`
- Integration Method: `GET`
- Routes: `$connect`, `$disconnect`, `$default` all configured

---

## Possible Issues

### 1. Query Parameter Substitution
**Issue**: API Gateway WebSocket might not support `$request.querystring.session_id` variable substitution in integration URI.

**Solution**: API Gateway should automatically append query parameters, but the integration URI format might be wrong.

### 2. WebSocket Upgrade Handshake
**Issue**: HTTP_PROXY integration might not properly handle WebSocket upgrade handshake.

**Solution**: May need to configure integration differently or use a different integration type.

### 3. Backend Endpoint Compatibility
**Issue**: The backend `/ws` endpoint expects query parameters, but API Gateway might not be forwarding them correctly.

**Solution**: Verify backend can handle the connection without query params, or configure API Gateway to pass them.

---

## Next Steps to Debug

1. **Check API Gateway Logs**
   - Enable CloudWatch logs for WebSocket API
   - Check for connection errors

2. **Test Integration URI Format**
   - Try: `http://13.58.115.166:8000/ws` (base URI, let API Gateway append query)
   - Try: `http://13.58.115.166:8000/ws?session_id={session_id}` (template format)

3. **Verify Backend Accepts Connection**
   - Check if backend receives connection attempts
   - Check backend logs for WebSocket connection errors

4. **Alternative: Use Path Parameter**
   - Configure API Gateway to extract session_id from query
   - Use path parameter format: `/ws/{session_id}`
   - Requires route configuration to extract and transform

---

## Current Configuration

**Integration**:
- URI: `http://13.58.115.166:8000/ws?session_id=$request.querystring.session_id`
- Type: `HTTP_PROXY`
- Method: `GET`

**Routes**:
- `$connect` → Integration
- `$disconnect` → Integration  
- `$default` → Integration

---

## Updates (Nov 20, 2025)

### Backend now supports registration-by-message
- `/ws` no longer requires a `session_id` query parameter.
- Clients send `{ "type": "register", "sessionID": "<id>" }` immediately after `onopen`.
- Works for both direct connections and local test UI (`backend/scaffoldtest_ui.html`).

### CloudWatch logging enabled
- Log group: `/aws/apigateway/927uc04ep5`
- Example entries:
  - `status":"403", routeKey:"-"` for earlier attempts with query/path parameters.
  - `status":"404", routeKey:"$connect"` for latest attempt hitting `/prod` root.

### Key finding
- API Gateway WebSocket with `HTTP_PROXY` integration **does not perform a WebSocket upgrade** to the target URL. It issues a plain HTTP `GET /ws` (no `Connection: Upgrade`), so FastAPI returns HTTP 404. CloudWatch confirms API Gateway receives the 404 from the integration.
- Result: API Gateway **cannot proxy directly** to the FastAPI WebSocket endpoint using `HTTP_PROXY`.

### Implications
1. To keep using API Gateway WebSocket, we must integrate with Lambda (`AWS_PROXY`) or another AWS service that handles connections natively, then relay messages via `@connections`.
2. Alternatively, skip API Gateway for WebSocket traffic and connect clients directly to `wss://<ec2-host>/ws`.
3. ALB/NLB with WebSocket support could also sit in front of EC2 if static IP / HTTPS termination is required.

### Next Actions
1. Decide whether to:
   - Implement a Lambda-based WebSocket hub (more work, but keeps AWS-managed endpoint), or
   - Expose the FastAPI WebSocket through ALB/CloudFront and update clients to use that URL.
2. If staying with API Gateway, design the Lambda flow:
   - `$connect`: store `connectionId` + `sessionID` (from register message) in DynamoDB.
   - Backend pushes updates via REST call to a Lambda/lite service that invokes `@connections`.
   - `$disconnect`: clean up connection records.
3. If bypassing API Gateway, ensure HTTPS/WebSocket termination via ALB + ACM certificate.

**Status**: HTTP proxy approach ruled out. Need architectural decision (Lambda hub vs. direct EC2 WebSocket).

