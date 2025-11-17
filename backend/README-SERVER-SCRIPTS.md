# Server Management Scripts

Two PowerShell scripts are provided to manage the backend server:

## stop-server.ps1

Stops all backend server instances running on port 8000.

**Usage:**
```powershell
.\stop-server.ps1
```

This script will:
- Find all processes listening on port 8000
- Stop each process
- Verify they're stopped

## start-server.ps1

Starts a single instance of the backend server.

**Usage:**
```powershell
.\start-server.ps1
```

This script will:
- Check if port 8000 is already in use (and warn if it is)
- Verify Python and uvicorn are installed
- Start the server on `http://localhost:8000` with auto-reload enabled
- Display the server URL and instructions

**Note:** If port 8000 is already in use, run `stop-server.ps1` first.

## Quick Start

1. **Stop any existing servers:**
   ```powershell
   cd backend
   .\stop-server.ps1
   ```

2. **Start the server:**
   ```powershell
   .\start-server.ps1
   ```

The server will be available at `http://localhost:8000` and will automatically reload when code changes are detected.


