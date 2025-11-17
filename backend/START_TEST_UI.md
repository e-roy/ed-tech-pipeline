# How to Start the Test UI

## Quick Start

### Step 1: Start the Backend Server

Open a terminal in the `backend` directory and run:

```powershell
# Windows PowerShell
cd C:\Users\franc\Documents\Github\pipeline\backend
uvicorn app.main:app --reload --host localhost --port 8000
```

Or if you have a virtual environment:

```powershell
# Activate virtual environment first (if you have one)
.\venv\Scripts\Activate.ps1
# Then start the server
uvicorn app.main:app --reload --host localhost --port 8000
```

The server will start on `http://localhost:8000`

### Step 2: Open the Test UI

Simply open `backend/test_ui.html` in your browser:

**Option 1: Double-click**
- Navigate to `backend/test_ui.html` in Windows Explorer
- Double-click to open in your default browser

**Option 2: Drag and Drop**
- Drag `backend/test_ui.html` into Chrome/Firefox/Edge

**Option 3: Right-click → Open With**
- Right-click `backend/test_ui.html`
- Select "Open with" → Choose your browser

**Option 4: From Browser**
- Open your browser
- Press `Ctrl+O` (or File → Open)
- Navigate to `backend/test_ui.html`

## What the Test UI Does

The Test UI allows you to:
1. **Create Scripts** - Generate 4-part educational scripts (hook, concept, process, conclusion)
2. **Generate Audio** - Create TTS audio for each script part
3. **Generate Images** - Create images for video production
4. **Compose Videos** - Combine audio, images, and text into final videos

## Troubleshooting

### Backend Not Starting
- Make sure you're in the `backend` directory
- Check that Python 3.11+ is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Check if port 8000 is already in use

### Test UI Can't Connect
- Verify backend is running: Open `http://localhost:8000` in browser (should show API docs)
- Check browser console (F12) for errors
- Make sure CORS is configured (should be automatic)

### Authentication Issues
- The test UI uses `test@example.com` as default user
- Make sure this user exists in your database
- Or modify the email in the test UI form

## API Endpoints Used

The test UI connects to:
- `POST /api/generation/generate-audio` - Audio generation
- `POST /api/generation/generate-images` - Image generation
- `POST /api/generation/compose-video` - Video composition
- `POST /api/test/save-script` - Save test scripts

All endpoints expect the backend to be running on `http://localhost:8000`

