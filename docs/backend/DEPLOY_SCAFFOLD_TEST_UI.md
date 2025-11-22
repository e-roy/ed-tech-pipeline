# Scaffold Test UI - Deployment & Access Guide

## Quick Access

Once the backend is running, access the test UI at:
- **Local**: `http://localhost:8000/scaffoldtest`
- **Deployed Server**: `http://YOUR_SERVER_IP:8000/scaffoldtest` or `http://YOUR_DOMAIN/scaffoldtest` (if using nginx)

## Local Deployment

### Option 1: Using PowerShell Script (Recommended)

```powershell
cd backend
.\start-server.ps1
```

Then open: `http://localhost:8000/scaffoldtest`

### Option 2: Manual Start

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open: `http://localhost:8000/scaffoldtest`

## Server Deployment (EC2)

### Step 1: Deploy Code

Use the existing deployment script:

```powershell
.\deploy_simple.ps1
```

Or manually:

```powershell
# SSH to server (use your SSH key and server details)
ssh -i YOUR_SSH_KEY.pem YOUR_USER@YOUR_SERVER_IP

# Navigate to project
cd /opt/pipeline

# Pull latest code
sudo git fetch origin
sudo git reset --hard origin/master  # or your branch name

# Restart service
sudo systemctl restart pipeline-backend

# Check status
sudo systemctl status pipeline-backend
```

### Step 2: Access the Test UI

Once deployed, access at:
- **Direct**: `http://YOUR_SERVER_IP:8000/scaffoldtest`
- **Via Nginx** (if configured): `http://YOUR_DOMAIN/scaffoldtest`

### Step 3: Verify WebSocket Support

The nginx configuration (`backend/pipeline-backend.nginx`) already includes WebSocket support, so if you're using nginx as a reverse proxy, WebSockets should work automatically.

## Testing the UI

1. **Fill in the form** with test data:
   - User ID: `test-user-123`
   - Session ID: `test-session-456`
   - Template ID: `template-001`
   - Chosen Diagram ID: `diagram-002`
   - Script ID: `script-003`

2. **Click "Start Processing"**

3. **Watch the status lights**:
   - Agent2 will start (blinking red) → process (solid yellow) → finish (solid green)
   - Then Agent4 will follow the same pattern
   - Then Agent5 will follow the same pattern

4. **Check WebSocket connection**:
   - The connection status at the bottom should show "Connected"
   - If disconnected, it will automatically attempt to reconnect

## Troubleshooting

### WebSocket Connection Issues

If WebSocket fails to connect:

1. **Check firewall**: Ensure port 8000 is open
2. **Check nginx config**: If using nginx, verify WebSocket headers are set
3. **Check browser console**: Open DevTools (F12) and check for errors
4. **Verify server is running**: `curl http://localhost:8000/health`

### CORS Issues

If you see CORS errors, the backend already has CORS configured to allow all origins. If issues persist, check:
- The backend is running
- The correct port is being used
- No firewall is blocking the connection

## API Endpoints

- **Test UI**: `GET /scaffoldtest`
- **Start Processing**: `POST /api/startprocessing`
- **WebSocket**: `WS /ws/{session_id}`
- **Health Check**: `GET /health`

## Notes

- The test UI automatically detects the API base URL from `window.location.origin`
- WebSocket connections automatically reconnect if disconnected (up to 5 attempts)
- All agent status updates are sent via WebSocket in real-time
- Error messages are displayed below each agent status light if an error occurs

