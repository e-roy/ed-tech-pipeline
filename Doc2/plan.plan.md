<!-- 804347b6-4439-4447-be2c-cb1749111355 fab83728-b812-40da-9d77-9a401641c606 -->
# Orchestrator Integration for Full Pipeline Test

## Overview

Extend existing `VideoGenerationOrchestrator` to coordinate the Full Test pipeline. The orchestrator will manage Agent2 and Agent4 execution in parallel using status callbacks, then Agent5 sequentially, send its own status updates, create S3 folder structure, and forward standardized agent status updates to the WebSocket for UI display.

## Standard Status Message Format

All status messages (orchestrator and agents) will use this standardized format:

```json
{
  "agentnumber": "Orchestrator" | "Agent2" | "Agent4" | "Agent5",
  "userID": "string",
  "sessionID": "string",
  "status": "starting" | "processing" | "finished" | "error",
  "timestamp": 1234567890,
  "error": "string (optional, only if status=error)",
  "reason": "string (optional, only if status=error)",
  "videoUrl": "string (optional, in finished status)",
  "progress": "number (optional)",
  "fileCount": "number (optional)",
  "cost": "number (optional)",
  "other UI info": "..."
}
```

## Implementation Steps

### 1. Add Full Test Method to Existing Orchestrator

- **File**: `backend/app/services/orchestrator.py`
- Add `start_full_test_process()` method to `VideoGenerationOrchestrator` class:
  - Accepts `userId`, `sessionId`, `db` (database session)
  - Sends orchestrator status: `{agentnumber: "Orchestrator", userID, sessionID, status: "starting"}`
  - Creates S3 folder: `scaffold_test/{userId}/{sessionId}/` if it doesn't exist
  - Creates `timestamp.json` with raw Unix timestamp value (integer)
  - Creates status callback function that standardizes and forwards agent status to WebSocket
  - Triggers Agent2 and Agent4 in parallel using `asyncio.gather()` with error handling:
    - If either agent fails, stop immediately and send orchestrator error status
    - If both succeed, proceed to Agent5
  - Passes status callback to Agent2, Agent4, and Agent5
  - After Agent2+Agent4 complete successfully, triggers Agent5 synchronously
  - Sends orchestrator finished status after Agent5 completes (includes video link and all UI info)
  - If Agent5 fails, sends orchestrator error status

**Best Practice for Status Callbacks**: Pass a callback function to agents for status updates. This is better than:

- Direct WebSocket access: Decouples agents from WebSocket implementation, easier testing
- Orchestrator polling: More efficient, real-time updates, explicit control
- Callbacks allow orchestrator to standardize format before forwarding

### 2. Update API Endpoint `/api/startprocess`

- **File**: `backend/app/main.py`
- Modify the "Full Test" handler in `start_processing()` endpoint:
  - Create orchestrator instance: `VideoGenerationOrchestrator(websocket_manager)`
  - Call `orchestrator.start_full_test_process(userId, sessionId, db)` in background task
  - Return 200 immediately after triggering orchestrator (async background task)

### 3. Update Agent2 to Use Callback and Query Database

- **File**: `backend/app/agents/agent_2.py`
- Modify `agent_2_process()` to:
  - Accept `db` parameter (database session)
  - Accept `status_callback` parameter (function for sending status to orchestrator)
  - Query `video_session` table: `SELECT * FROM video_session WHERE id = :session_id AND user_id = :user_id`
  - If row doesn't exist, raise error immediately
  - Use the row data for processing
  - Update S3 output path to: `scaffold_test/{userId}/{sessionId}/agent2/`
  - Send all status updates via `status_callback()` instead of directly to websocket_manager
  - Remove call to Agent4 (orchestrator handles this)
  - Return completion status/result when finished (for orchestrator to track)

### 4. Update Agent4 to Use Callback and Query Database

- **File**: `backend/app/agents/agent_4.py`
- Modify `agent_4_process()` to:
  - Accept `db` parameter (database session)
  - Accept `status_callback` parameter (function for sending status to orchestrator)
  - Query `video_session` table: `SELECT * FROM video_session WHERE id = :session_id AND user_id = :user_id`
  - If row doesn't exist, raise error immediately
  - Use the row data for processing
  - Update S3 output path to: `scaffold_test/{userId}/{sessionId}/agent4/`
  - Send all status updates via `status_callback()` instead of directly to websocket_manager
  - Remove call to Agent5 (orchestrator handles this)
  - Return completion status/result when finished (for orchestrator to track)

### 5. Update Agent5 for Orchestrator Integration

- **File**: `backend/app/agents/agent_5.py` (or wherever Agent5 is defined)
- Modify `agent_5_process()` to:
  - Accept `db` parameter (database session)
  - Accept `status_callback` parameter (function for sending status to orchestrator)
  - Scan S3 folders: `scaffold_test/{userId}/{sessionId}/agent2/` and `agent4/` to discover content
  - Send all status updates via `status_callback()` instead of directly to websocket_manager
  - Include video link in final status message (for scaffoldtest UI)
  - Return completion status with video link and all relevant information

### 6. Implement Status Callback in Orchestrator

- **File**: `backend/app/services/orchestrator.py`
- In `start_full_test_process()`:
  - Create status callback function that:
    - Receives status data from agents
    - Ensures standard format with `agentnumber`, `userID`, `sessionID`, `status`, `timestamp`
    - Adds any additional scaffoldtest UI information (progress, file counts, costs, video link, etc.)
    - Forwards standardized messages to WebSocket via websocket_manager
  - Pass this callback to Agent2, Agent4, and Agent5
  - Handle orchestrator's own status messages in same standard format
  - Include video link in orchestrator finished status (from Agent5 result)
  - Include all relevant information for scaffoldtest UI in status messages

### 7. Update ScaffoldTest UI for Orchestrator Status and Standard Format

- **File**: `backend/scaffoldtest_ui.html`
- Add orchestrator status indicator:
  - Add new status light element for "Orchestrator" in the status section
  - Update `updateAgentStatus()` function to handle "Orchestrator" as agentnumber
  - Update WebSocket message handler to parse standard format
  - Ensure all status messages (orchestrator, Agent2, Agent4, Agent5) use same lighting logic:
    - `starting` = red blinking
    - `processing` = yellow solid
    - `finished` = green solid
    - `error` = red solid
  - Display video link when received in finished status
  - Display all UI information (progress, costs, file counts, etc.) when available

### 8. S3 Folder Structure and timestamp.json

- **File**: `backend/app/services/orchestrator.py`
- In `start_full_test_process()`:
  - Create S3 folder: `scaffold_test/{userId}/{sessionId}/` if it doesn't exist
  - Create `timestamp.json` with raw timestamp value (Unix timestamp or ISO8601 string)
  - Use StorageService to create folder and upload timestamp.json

### 9. Database Connection for Agents

- Ensure Agent2, Agent4, and Agent5 receive database session from orchestrator
- Use same database connection (Neon PostgreSQL) as backend API
- Pass `db` session from `get_db()` dependency to orchestrator, then to agents
- Query pattern: `SELECT * FROM video_session WHERE id = :session_id AND user_id = :user_id`
- If query returns no row, raise error immediately

## Key Files to Modify

1. `backend/app/services/orchestrator.py` - Add `start_full_test_process()` method with status callback
2. `backend/app/main.py` - Update `/api/startprocess` endpoint to use orchestrator
3. `backend/app/agents/agent_2.py` - Add database query, update S3 paths, use status callback, remove Agent4 call
4. `backend/app/agents/agent_4.py` - Add database query, update S3 paths, use status callback, remove Agent5 call
5. `backend/app/agents/agent_5.py` - Add status callback, scan S3 folders, include video link
6. `backend/scaffoldtest_ui.html` - Add orchestrator status UI, update to handle standard format with video link

## Technical Decisions

- **Agent Status Communication**: Callback function pattern (best practice - decouples agents from orchestrator, easier testing, dependency injection)
- **Agent Execution**: Parallel execution of Agent2+Agent4 using `asyncio.gather()`, then sequential Agent5
- **S3 Path**: `scaffold_test/{userId}/{sessionId}/` (matches existing pattern)
- **timestamp.json**: Raw timestamp value (Unix timestamp or ISO8601 string)
- **Status Format**: Standardized object with `agentnumber`, `userID`, `sessionID`, `status`, `timestamp`, plus scaffoldtest UI info (progress, costs, file counts, video link)
- **Database**: Same Neon PostgreSQL connection via `get_db()` dependency
- **Error Handling**: Stop immediately if Agent2 or Agent4 fails, send orchestrator error status
- **Agent5 Discovery**: Agent5 scans S3 folders to discover Agent2 and Agent4 output
- **Video Link**: Included in both Agent5 finished status and orchestrator finished status
- **Orchestrator Finished**: Sent after Agent5 completes (not after Agent2+Agent4)

### To-dos

- [ ] Create orchestrator function that manages Full Test process: sends status updates, creates S3 folder, triggers agents in parallel
- [ ] Update /api/startprocess endpoint to call orchestrator function and return 200 immediately
- [ ] Update Agent2 to query video_session table and output to s3/{userId}/{sessionId}/agent2/
- [ ] Update Agent4 to query video_session table and output to s3/{userId}/{sessionId}/agent4/
- [ ] Add orchestrator status indicator to scaffoldtest UI with same lighting logic
- [ ] Implement agent status forwarding from orchestrator to WebSocket
- [ ] Create S3 folder structure and timestamp.json file in orchestrator
- [ ] Implement agent completion notification mechanism (agents notify orchestrator when done)