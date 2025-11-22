<!-- bdc97458-bcab-4e92-aec6-dbc84228a84b 53565bbe-c1c0-481b-8475-1936d6394104 -->
# Agent 6 Fallback Agent Implementation Plan

## Overview

Create Agent 6 as a fallback agent that automatically triggers when Agent 5 fails. Agent 6 uses DALL-E for image generation, converts images to video clips, stitches them with AWS MediaConvert, and logs to CloudWatch.

## Implementation Steps

### 1. Create Agent 6 Module (`backend/app/agents/agent_6.py`)

**Core Function: `agent_6_process()`**

- Signature matches `agent_5_process()` for compatibility
- Parameters: `websocket_manager`, `user_id`, `session_id`, `supersessionid`, `storage_service`, `pipeline_data`, `db`, `status_callback`
- Read same inputs as Agent 5:
  - Load `storyboard.json` from `scaffold_test/{user_id}/{session_id}/agent2/storyboard.json`
  - Load audio files from `scaffold_test/{user_id}/{session_id}/agent4/`
  - Extract segments with `visual_guidance`, `duration`, `narration`

**Video Generation Flow:**

1. Parse storyboard segments
2. Generate DALL-E images in parallel (batches of 2, matching Agent 5)

   - Use `visual_guidance` as prompt
   - Generate 1920x1024 images (DALL-E max size, will scale to 1080p)
   - Save to temp directory

3. Convert images to video clips:

   - Use ffmpeg to create silent video clips matching segment duration
   - Format: MP4, H.264, 1920x1080, 30fps
   - Upload each clip to S3: `scaffold_test/{user_id}/{session_id}/agent5/{segment_id}_clip.mp4`

4. Replace audio in clips:

   - Download narration audio from Agent4 S3 paths
   - Use ffmpeg to replace audio in each clip (trim/pad to match duration)
   - Re-upload to S3

**Status Updates:**

- Use same `status_callback` interface as Agent 5
- Send updates: "starting", "processing" (with progress), "finished" (with videoUrl), "error"
- Agent number: "Agent6"
- Include cost estimates in status messages

### 2. AWS MediaConvert Service (`backend/app/services/mediaconvert_service.py`)

**Class: `MediaConvertService`**

- Initialize boto3 MediaConvert client using AWS profile `default2`
- Methods:
  - `create_job_role()`: Create IAM role for MediaConvert with S3 read/write permissions
  - `setup_iam_permissions()`: Ensure IAM role exists and has required policies
  - `create_stitch_job()`: Create MediaConvert job to concatenate video clips
    - Input: List of S3 URIs for video clips
    - Output: Single MP4 in S3
    - Settings: H.264, 1920x1080, 5000k bitrate, 30fps
    - Audio: Replace with narration audio (from Agent4)
    - Concat mode: "simple" (default) or "fade" (parameterized)
  - `wait_for_job_completion()`: Poll job status until complete
  - `get_job_output_uri()`: Return S3 URI of final stitched video

**IAM Setup:**

- Role name: `MediaConvertJobRole` (or parameterized)
- Policies: S3 read/write for bucket, MediaConvert job creation
- Use boto3 IAM client to create/verify role

### 3. CloudWatch Logging (`backend/app/services/cloudwatch_logger.py`)

**Class: `CloudWatchLogger`**

- Initialize boto3 CloudWatch Logs client
- Log group: `/pipeline/agent6`
- Methods:
  - `log_segment_generation()`: Log per-segment success/failure (JSON format)
  - `log_mediaconvert_job()`: Log MediaConvert job status, job ID, output URI
  - `log_final_video()`: Log final stitched video URI
  - `log_cost_breakdown()`: Log cost estimates per segment and total
- JSON format: `{"timestamp": "...", "event_type": "...", "data": {...}}`

### 4. Cost Tracking

**Cost Estimates (fixed):**

- DALL-E image: $0.02 per image (DALL-E 2 pricing)
- Video clip creation: $0.001 per clip (processing cost)
- MediaConvert stitching: $0.01 per job (estimated)
- Total per 60s video: ~$0.10-0.15 (4 segments)

**Track in Agent 6:**

- Per-segment cost: DALL-E + clip creation
- MediaConvert cost: Fixed estimate
- Total cost: Sum of all segments + MediaConvert
- Include in status messages and CloudWatch logs

### 5. Orchestrator Integration (`backend/app/services/orchestrator.py`)

**Modify `start_full_test_process()`:**

- Wrap Agent 5 call in try/except
- On Agent 5 exception:
  ```python
  try:
      await agent_5_process(...)
  except Exception as e:
      logger.error(f"Agent5 failed: {e}, triggering Agent6 fallback")
      await self._send_orchestrator_status(userId, sessionId, "processing", 
          {"message": "Agent5 failed, starting Agent6 fallback..."})
      from app.agents.agent_6 import agent_6_process
      await agent_6_process(...)  # Same parameters as Agent 5
  ```


**Modify `run_agent_5_with_error_handling()` in `backend/app/main.py`:**

- Similar try/except pattern
- Call Agent 6 on Agent 5 failure

### 6. ScaffoldTest UI Updates (`backend/scaffoldtest_ui.html`)

**Add Agent6 Status Row:**

- Add HTML for Agent6 status (initially hidden)
- Show only when Agent5 status is "error"
- Same status light pattern (starting/processing/finished/error)

**Cost Display:**

- Add cost tracking object: `window.agentCosts = { Agent2: 0, Agent4: 0, Agent5: 0, Agent6: 0 }`
- Update costs from WebSocket messages (if `cost` field present)
- Display cost per agent in status section
- Display total cost at bottom
- Format: "Agent2: $0.01 | Agent4: $0.05 | Agent5: $0.15 | Agent6: $0.12 | Total: $0.33"

**JavaScript Updates:**

- Listen for Agent6 status messages
- Show/hide Agent6 row based on Agent5 error state
- Update cost display on each agent completion

### 7. Dependencies

**Add to `backend/requirements.txt`:**

- `boto3` (already present, verify version supports MediaConvert)
- No new dependencies needed (DALL-E via existing OpenAI client)

**Environment Variables:**

- Use existing AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
- Use existing OPENAI_API_KEY for DALL-E
- MediaConvert will use AWS profile `default2` (via boto3 session)

### 8. File Structure

```
backend/app/
├── agents/
│   └── agent_6.py              # New: Agent 6 implementation
├── services/
│   ├── mediaconvert_service.py  # New: MediaConvert integration
│   └── cloudwatch_logger.py    # New: CloudWatch logging
```

### 9. Error Handling

- Agent 6 failures: Raise exception (same as Agent 5)
- MediaConvert job failures: Log to CloudWatch, raise exception
- DALL-E API failures: Retry once, then raise exception
- Audio replacement failures: Log warning, continue without audio replacement

### 10. Testing Considerations

- Test with Agent 5 failure simulation
- Verify MediaConvert job creation and completion
- Verify CloudWatch logs are created
- Verify cost tracking in UI
- Verify Agent6 row appears/disappears correctly

## Key Files to Modify

1. `backend/app/agents/agent_6.py` - New file
2. `backend/app/services/mediaconvert_service.py` - New file  
3. `backend/app/services/cloudwatch_logger.py` - New file
4. `backend/app/services/orchestrator.py` - Add Agent 6 fallback logic
5. `backend/app/main.py` - Add Agent 6 fallback in `run_agent_5_with_error_handling()`
6. `backend/scaffoldtest_ui.html` - Add Agent6 UI and cost tracking
7. `backend/requirements.txt` - Verify boto3 version

## Notes

- Agent 6 uses same S3 paths as Agent 5 for compatibility
- Status callback interface preserved for seamless integration
- Cost estimates are fixed (not calculated from actual API costs)
- MediaConvert IAM setup happens automatically on first use
- CloudWatch log group created automatically if it doesn't exist

### To-dos

- [ ] Create agent_6.py with core process function, DALL-E image generation, and video clip creation
- [ ] Create mediaconvert_service.py with IAM setup, job creation, and stitching logic
- [ ] Create cloudwatch_logger.py with JSON logging for segments, MediaConvert jobs, and costs
- [ ] Add Agent 6 fallback logic to orchestrator.py when Agent 5 fails
- [ ] Add Agent 6 fallback logic to main.py run_agent_5_with_error_handling function
- [ ] Update scaffoldtest_ui.html to show Agent6 status row and cost tracking display
- [ ] Test Agent 6 triggers correctly when Agent 5 fails, MediaConvert works, and UI updates properly