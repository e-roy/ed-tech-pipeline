# Phase 2: Core Agent Implementation - Tasks

## Overview
This phase implements the core multi-agent system including the Prompt Parser Agent, Batch Image Generator Agent, and the Video Generation Orchestrator for the image generation flow.

**Estimated Time:** 10 hours
**Dependencies:** Phase 1 completed

---

## Task Checklist

### 1. Base Agent Interface (Hour 6-6.5)
**Estimated Time:** 30 minutes | **Dependencies:** Phase 1 completed

- [ ] **1.1 Create Base Agent Protocol**
  - [ ] 1.1.1 Create `agents/base.py` file
  - [ ] 1.1.2 Import Protocol from typing
  - [ ] 1.1.3 Import AgentInput and AgentOutput from schemas
  - [ ] 1.1.4 Define `Agent` protocol class
  - [ ] 1.1.5 Add `process()` method signature with async
  - [ ] 1.1.6 Add type hints: `async def process(self, input: AgentInput) -> AgentOutput`
  - [ ] 1.1.7 Add docstring explaining Agent protocol
  - [ ] 1.1.8 Add protocol implementation note for future compatibility
  - [ ] 1.1.9 Test protocol definition (ensure no syntax errors)

---

### 2. Prompt Parser Agent (Hour 6.5-8.5)
**Estimated Time:** 2 hours | **Dependencies:** Task 1 completed

- [ ] **2.1 Create Prompt Parser Agent Class**
  - [ ] 2.1.1 Create `agents/prompt_parser.py` file
  - [ ] 2.1.2 Import required modules (random, json, time, replicate)
  - [ ] 2.1.3 Import AgentInput, AgentOutput from schemas
  - [ ] 2.1.4 Import settings from config
  - [ ] 2.1.5 Create `PromptParserAgent` class
  - [ ] 2.1.6 Add __init__ method
  - [ ] 2.1.7 Set self.model = "meta/meta-llama-3.1-70b-instruct"
  - [ ] 2.1.8 Add class docstring

- [ ] **2.2 Implement Process Method**
  - [ ] 2.2.1 Define async `process()` method with AgentInput parameter
  - [ ] 2.2.2 Add try-except block for error handling
  - [ ] 2.2.3 Start timer: `start_time = time.time()`
  - [ ] 2.2.4 Extract user_prompt from input.data
  - [ ] 2.2.5 Extract num_images from input.data.options (default 6)
  - [ ] 2.2.6 Generate consistency seed: `random.randint(100000, 999999)`
  - [ ] 2.2.7 Call `_build_system_prompt(num_images)`
  - [ ] 2.2.8 Call `await _call_llm(system_prompt, user_prompt)`
  - [ ] 2.2.9 Parse JSON response from LLM
  - [ ] 2.2.10 Add consistency_seed to each image_prompt
  - [ ] 2.2.11 Add guidance_scale (7.5) to each prompt
  - [ ] 2.2.12 Add variation_strength (0.3) to each prompt
  - [ ] 2.2.13 Calculate duration: `time.time() - start_time`
  - [ ] 2.2.14 Build AgentOutput with success=True
  - [ ] 2.2.15 Set cost=0.001 for Llama 3.1
  - [ ] 2.2.16 Return AgentOutput
  - [ ] 2.2.17 Handle exceptions and return error AgentOutput

- [ ] **2.3 Implement System Prompt Builder**
  - [ ] 2.3.1 Define `_build_system_prompt()` method
  - [ ] 2.3.2 Accept num_images parameter
  - [ ] 2.3.3 Create multi-line system prompt string
  - [ ] 2.3.4 Include role: "product photography AI assistant"
  - [ ] 2.3.5 Add task: generate N distinct prompts for different views
  - [ ] 2.3.6 Add rule: maintain visual consistency
  - [ ] 2.3.7 Add rule: use professional photography terminology
  - [ ] 2.3.8 Add rule: vary only angle/view
  - [ ] 2.3.9 Add rule: output valid JSON only
  - [ ] 2.3.10 Define exact JSON output structure
  - [ ] 2.3.11 Include view_type field explanation
  - [ ] 2.3.12 Return formatted system prompt string

- [ ] **2.4 Implement LLM API Call**
  - [ ] 2.4.1 Define async `_call_llm()` method
  - [ ] 2.4.2 Accept system_prompt and user_prompt parameters
  - [ ] 2.4.3 Build full_prompt combining system and user prompts
  - [ ] 2.4.4 Set up Replicate API call with async_run
  - [ ] 2.4.5 Configure model: self.model
  - [ ] 2.4.6 Set prompt parameter
  - [ ] 2.4.7 Set max_tokens=2000
  - [ ] 2.4.8 Set temperature=0.7
  - [ ] 2.4.9 Set top_p=0.9
  - [ ] 2.4.10 Set system_prompt parameter
  - [ ] 2.4.11 Execute API call with await
  - [ ] 2.4.12 Concatenate streaming output: `"".join(output)`
  - [ ] 2.4.13 Extract JSON from response (find first '{' and last '}')
  - [ ] 2.4.14 Parse JSON string with json.loads()
  - [ ] 2.4.15 Handle JSON parse errors
  - [ ] 2.4.16 Return parsed dictionary

- [ ] **2.5 Test Prompt Parser Agent**
  - [ ] 2.5.1 Create test script or use pytest
  - [ ] 2.5.2 Import PromptParserAgent
  - [ ] 2.5.3 Create AgentInput with test prompt: "pink tennis shoes"
  - [ ] 2.5.4 Set num_images=4 for faster testing
  - [ ] 2.5.5 Instantiate agent: `agent = PromptParserAgent()`
  - [ ] 2.5.6 Call `result = await agent.process(input)`
  - [ ] 2.5.7 Assert result.success is True
  - [ ] 2.5.8 Assert consistency_seed is not None
  - [ ] 2.5.9 Assert len(image_prompts) == 4
  - [ ] 2.5.10 Assert all prompts have same seed
  - [ ] 2.5.11 Print sample output to review quality
  - [ ] 2.5.12 Verify different view_types are generated
  - [ ] 2.5.13 Test with different product descriptions
  - [ ] 2.5.14 Test error handling with invalid input

---

### 3. Batch Image Generator Agent (Hour 8.5-10.5)
**Estimated Time:** 2 hours | **Dependencies:** Task 2 completed

- [ ] **3.1 Create Batch Image Generator Class**
  - [ ] 3.1.1 Create `agents/image_generator.py` file
  - [ ] 3.1.2 Import required modules (asyncio, time, uuid, replicate)
  - [ ] 3.1.3 Import AgentInput, AgentOutput
  - [ ] 3.1.4 Import settings
  - [ ] 3.1.5 Create `BatchImageGeneratorAgent` class
  - [ ] 3.1.6 Add __init__ method
  - [ ] 3.1.7 Define self.models dictionary with flux-pro and sdxl
  - [ ] 3.1.8 Set flux-pro model ID: "black-forest-labs/flux-pro"
  - [ ] 3.1.9 Set sdxl model ID (with version hash)
  - [ ] 3.1.10 Add class docstring

- [ ] **3.2 Implement Process Method**
  - [ ] 3.2.1 Define async `process()` method
  - [ ] 3.2.2 Add try-except block
  - [ ] 3.2.3 Start timer
  - [ ] 3.2.4 Extract image_prompts from input.data
  - [ ] 3.2.5 Extract model_name (default: "flux-pro")
  - [ ] 3.2.6 Create empty tasks list
  - [ ] 3.2.7 Loop through each prompt_data in image_prompts
  - [ ] 3.2.8 Create task for each: `_generate_single_image(model, prompt_data)`
  - [ ] 3.2.9 Append task to tasks list
  - [ ] 3.2.10 Execute parallel: `results = await asyncio.gather(*tasks, return_exceptions=True)`
  - [ ] 3.2.11 Process results loop
  - [ ] 3.2.12 Check if result is Exception
  - [ ] 3.2.13 Log error and continue for exceptions
  - [ ] 3.2.14 Append successful results to images list
  - [ ] 3.2.15 Sum total_cost from all results
  - [ ] 3.2.16 Calculate total duration
  - [ ] 3.2.17 Check if any images succeeded
  - [ ] 3.2.18 Return AgentOutput with images and costs
  - [ ] 3.2.19 Handle complete failure case

- [ ] **3.3 Implement Single Image Generation**
  - [ ] 3.3.1 Define async `_generate_single_image()` method
  - [ ] 3.3.2 Accept model and prompt_data parameters
  - [ ] 3.3.3 Get model_id from self.models dictionary
  - [ ] 3.3.4 Start timer for single generation
  - [ ] 3.3.5 Build model_input for flux-pro (if model == "flux-pro")
  - [ ] 3.3.6 Set prompt, guidance, num_outputs, aspect_ratio, output_format
  - [ ] 3.3.7 Set output_quality, safety_tolerance, seed
  - [ ] 3.3.8 Build model_input for sdxl (else branch)
  - [ ] 3.3.9 Set prompt, negative_prompt, width, height
  - [ ] 3.3.10 Set guidance_scale, num_inference_steps, seed
  - [ ] 3.3.11 Call Replicate API: `await replicate.async_run(model_id, input=model_input)`
  - [ ] 3.3.12 Extract image URL from output (handle list or string)
  - [ ] 3.3.13 Calculate duration for this image
  - [ ] 3.3.14 Set cost ($0.05 for flux-pro, $0.01 for sdxl)
  - [ ] 3.3.15 Generate unique image ID: `img_{uuid.uuid4().hex[:8]}`
  - [ ] 3.3.16 Build result dictionary with all metadata
  - [ ] 3.3.17 Return result dictionary
  - [ ] 3.3.18 Handle exceptions and raise with context

- [ ] **3.4 Test Batch Image Generator**
  - [ ] 3.4.1 Create test with small prompt set (2 images)
  - [ ] 3.4.2 Use sdxl model for cheaper testing
  - [ ] 3.4.3 Create AgentInput with image_prompts
  - [ ] 3.4.4 Instantiate agent
  - [ ] 3.4.5 Call `result = await agent.process(input)`
  - [ ] 3.4.6 Assert result.success is True
  - [ ] 3.4.7 Assert len(images) == 2
  - [ ] 3.4.8 Assert all images have valid URLs (start with https://)
  - [ ] 3.4.9 Assert costs are reasonable
  - [ ] 3.4.10 Verify parallel execution (should be faster than sequential)
  - [ ] 3.4.11 Test error handling (invalid prompt)
  - [ ] 3.4.12 Verify partial success handling
  - [ ] 3.4.13 Download one image to verify it's valid
  - [ ] 3.4.14 Check image metadata

---

### 4. Video Generation Orchestrator (Hour 10.5-13)
**Estimated Time:** 2.5 hours | **Dependencies:** Tasks 2-3 completed

- [ ] **4.1 Create Orchestrator Class**
  - [ ] 4.1.1 Create `orchestrator/video_orchestrator.py` file
  - [ ] 4.1.2 Import asyncio, SQLAlchemy components
  - [ ] 4.1.3 Import database models (Session, Asset, AssetType, etc.)
  - [ ] 4.1.4 Import ws_manager
  - [ ] 4.1.5 Import PromptParserAgent
  - [ ] 4.1.6 Import BatchImageGeneratorAgent
  - [ ] 4.1.7 Import uuid
  - [ ] 4.1.8 Create `VideoGenerationOrchestrator` class
  - [ ] 4.1.9 Add __init__ with db parameter
  - [ ] 4.1.10 Initialize self.db = db
  - [ ] 4.1.11 Initialize self.prompt_parser = PromptParserAgent()
  - [ ] 4.1.12 Initialize self.image_generator = BatchImageGeneratorAgent()
  - [ ] 4.1.13 Add class docstring

- [ ] **4.2 Implement Image Generation Flow**
  - [ ] 4.2.1 Define async `generate_images()` method
  - [ ] 4.2.2 Accept session_id, user_prompt, num_images, style_keywords
  - [ ] 4.2.3 Add try-except wrapper
  - [ ] 4.2.4 Load session from database with `_get_session()`
  - [ ] 4.2.5 Update session.product_prompt
  - [ ] 4.2.6 Update session.stage to IMAGE_GENERATION
  - [ ] 4.2.7 Send WebSocket progress: "Analyzing your prompt..." (10%)
  - [ ] 4.2.8 Create AgentInput for prompt parser
  - [ ] 4.2.9 Call `parser_output = await self.prompt_parser.process(input)`
  - [ ] 4.2.10 Check parser_output.success
  - [ ] 4.2.11 Raise exception if failed
  - [ ] 4.2.12 Save consistency_seed to session
  - [ ] 4.2.13 Save style_keywords to session
  - [ ] 4.2.14 Log parsing cost with `_log_cost()`
  - [ ] 4.2.15 Send WebSocket progress: "Generating images..." (20%)
  - [ ] 4.2.16 Create AgentInput for image generator
  - [ ] 4.2.17 Call `generator_output = await self.image_generator.process(input)`
  - [ ] 4.2.18 Check generator_output.success
  - [ ] 4.2.19 Log generation cost
  - [ ] 4.2.20 Loop through generated images
  - [ ] 4.2.21 Send progress update for each image (20-50%)
  - [ ] 4.2.22 Create Asset object for each image
  - [ ] 4.2.23 Set asset fields (id, session_id, asset_type, url, metadata, cost)
  - [ ] 4.2.24 Add asset to database
  - [ ] 4.2.25 Append asset.id to generated_image_ids list
  - [ ] 4.2.26 Update session.generated_image_ids
  - [ ] 4.2.27 Update session.total_cost
  - [ ] 4.2.28 Update session.stage to IMAGE_SELECTION
  - [ ] 4.2.29 Commit database transaction
  - [ ] 4.2.30 Send final WebSocket progress: "Complete!" (100%)
  - [ ] 4.2.31 Include image data in progress message
  - [ ] 4.2.32 Return success status dictionary
  - [ ] 4.2.33 Handle errors with `_handle_error()`

- [ ] **4.3 Implement Helper Methods**
  - [ ] 4.3.1 Define async `_get_session()` method
  - [ ] 4.3.2 Query database for session by ID
  - [ ] 4.3.3 Use scalar_one_or_none()
  - [ ] 4.3.4 Raise exception if session not found
  - [ ] 4.3.5 Return session object
  - [ ] 4.3.6 Define async `_log_cost()` method
  - [ ] 4.3.7 Accept session_id, agent_name, model_used, cost, duration, success, error
  - [ ] 4.3.8 Create GenerationCost object
  - [ ] 4.3.9 Add to database
  - [ ] 4.3.10 Commit transaction
  - [ ] 4.3.11 Define async `_handle_error()` method
  - [ ] 4.3.12 Accept session_id, stage, error
  - [ ] 4.3.13 Load session
  - [ ] 4.3.14 Set session.stage to FAILED
  - [ ] 4.3.15 Commit transaction
  - [ ] 4.3.16 Send error WebSocket message
  - [ ] 4.3.17 Log error to console/file

- [ ] **4.4 Test Orchestrator**
  - [ ] 4.4.1 Create integration test
  - [ ] 4.4.2 Create test session in database
  - [ ] 4.4.3 Get database session (AsyncSession)
  - [ ] 4.4.4 Instantiate orchestrator with db
  - [ ] 4.4.5 Call `await orchestrator.generate_images()`
  - [ ] 4.4.6 Use small num_images (2-4) for testing
  - [ ] 4.4.7 Assert result["status"] == "success"
  - [ ] 4.4.8 Query database for updated session
  - [ ] 4.4.9 Assert generated_image_ids has correct count
  - [ ] 4.4.10 Assert total_cost > 0
  - [ ] 4.4.11 Assert consistency_seed is set
  - [ ] 4.4.12 Assert stage is IMAGE_SELECTION
  - [ ] 4.4.13 Verify assets were created in database
  - [ ] 4.4.14 Check GenerationCost entries exist
  - [ ] 4.4.15 Clean up test data

---

### 5. Generation API Endpoints (Hour 13-14.5)
**Estimated Time:** 1.5 hours | **Dependencies:** Task 4 completed

- [ ] **5.1 Create Generation Router**
  - [ ] 5.1.1 Create `routers/generation.py` file
  - [ ] 5.1.2 Import FastAPI components (APIRouter, Depends, HTTPException, BackgroundTasks)
  - [ ] 5.1.3 Import AsyncSession, get_db
  - [ ] 5.1.4 Import request/response schemas
  - [ ] 5.1.5 Import VideoGenerationOrchestrator
  - [ ] 5.1.6 Create APIRouter instance
  - [ ] 5.1.7 Add router to main.py imports

- [ ] **5.2 Implement Generate Images Endpoint**
  - [ ] 5.2.1 Define `@router.post("/generate-images")` endpoint
  - [ ] 5.2.2 Accept GenerateImagesRequest
  - [ ] 5.2.3 Accept BackgroundTasks dependency
  - [ ] 5.2.4 Accept db session dependency
  - [ ] 5.2.5 Create orchestrator instance
  - [ ] 5.2.6 Add background task: `orchestrator.generate_images()`
  - [ ] 5.2.7 Pass session_id, product_prompt, num_images, style_keywords
  - [ ] 5.2.8 Return immediate response (status: "processing")
  - [ ] 5.2.9 Include estimated_duration in response
  - [ ] 5.2.10 Add message about WebSocket updates
  - [ ] 5.2.11 Add error handling
  - [ ] 5.2.12 Test endpoint with curl or Postman

- [ ] **5.3 Implement Save Approved Images Endpoint**
  - [ ] 5.3.1 Define `@router.post("/save-approved-images")` endpoint
  - [ ] 5.3.2 Accept SaveApprovedImagesRequest
  - [ ] 5.3.3 Accept db session dependency
  - [ ] 5.3.4 Query session from database
  - [ ] 5.3.5 Handle session not found (404)
  - [ ] 5.3.6 Validate all image IDs exist in generated_image_ids
  - [ ] 5.3.7 Return 400 error if invalid IDs
  - [ ] 5.3.8 Update session.approved_image_ids
  - [ ] 5.3.9 Update session.stage to CLIP_GENERATION
  - [ ] 5.3.10 Commit transaction
  - [ ] 5.3.11 Return success response
  - [ ] 5.3.12 Include approved_count in response
  - [ ] 5.3.13 Test endpoint

- [ ] **5.4 Update Main App to Include Router**
  - [ ] 5.4.1 Import generation router in main.py
  - [ ] 5.4.2 Add `app.include_router(generation.router, prefix="/api", tags=["Generation"])`
  - [ ] 5.4.3 Restart server
  - [ ] 5.4.4 Check `/docs` for new endpoints
  - [ ] 5.4.5 Verify endpoint documentation is correct

---

### 6. End-to-End Testing (Hour 14.5-16)
**Estimated Time:** 1.5 hours | **Dependencies:** All above tasks completed

- [ ] **6.1 Manual E2E Test**
  - [ ] 6.1.1 Start backend server
  - [ ] 6.1.2 Open WebSocket connection with wscat
  - [ ] 6.1.3 Login to get token (curl/Postman)
  - [ ] 6.1.4 Create session (save session_id)
  - [ ] 6.1.5 Trigger image generation with test prompt
  - [ ] 6.1.6 Monitor WebSocket for progress updates
  - [ ] 6.1.7 Verify progress updates match expected stages
  - [ ] 6.1.8 Wait for completion message
  - [ ] 6.1.9 Check database for generated images
  - [ ] 6.1.10 Verify all image URLs are accessible
  - [ ] 6.1.11 Download one image to verify quality
  - [ ] 6.1.12 Call save-approved-images with selected IDs
  - [ ] 6.1.13 Verify session stage updated
  - [ ] 6.1.14 Check total cost is within expected range

- [ ] **6.2 Write Integration Test**
  - [ ] 6.2.1 Create `tests/test_integration.py`
  - [ ] 6.2.2 Import necessary modules
  - [ ] 6.2.3 Write async test function
  - [ ] 6.2.4 Create test session
  - [ ] 6.2.5 Instantiate orchestrator
  - [ ] 6.2.6 Call generate_images()
  - [ ] 6.2.7 Assert success
  - [ ] 6.2.8 Verify database state
  - [ ] 6.2.9 Clean up test data
  - [ ] 6.2.10 Run test: `pytest tests/test_integration.py -v`
  - [ ] 6.2.11 Verify test passes

- [ ] **6.3 Performance Testing**
  - [ ] 6.3.1 Time complete image generation flow
  - [ ] 6.3.2 Verify total time < 60 seconds for 6 images
  - [ ] 6.3.3 Check parallel execution is working (not sequential)
  - [ ] 6.3.4 Monitor CPU/memory usage
  - [ ] 6.3.5 Test with concurrent sessions (2-3 at once)
  - [ ] 6.3.6 Verify database connections are pooled correctly
  - [ ] 6.3.7 Check for memory leaks

- [ ] **6.4 Code Quality & Documentation**
  - [ ] 6.4.1 Run Black formatter on all new files
  - [ ] 6.4.2 Run Ruff linter
  - [ ] 6.4.3 Fix any issues
  - [ ] 6.4.4 Add docstrings to all classes and methods
  - [ ] 6.4.5 Add type hints everywhere
  - [ ] 6.4.6 Review code for security issues
  - [ ] 6.4.7 Check for hardcoded credentials
  - [ ] 6.4.8 Review error messages (no sensitive data)
  - [ ] 6.4.9 Commit all changes
  - [ ] 6.4.10 Push to GitHub
  - [ ] 6.4.11 Create checkpoint tag: `git tag phase-2-complete`

---

## Phase 2 Completion Criteria

✅ Prompt Parser Agent implemented and tested
✅ Batch Image Generator Agent implemented and tested
✅ Video Generation Orchestrator working for image flow
✅ `/api/generate-images` endpoint functional
✅ `/api/save-approved-images` endpoint functional
✅ WebSocket progress updates working throughout flow
✅ Database persistence working (sessions, assets, costs)
✅ Parallel image generation working (asyncio.gather)
✅ Cost tracking functional
✅ Unit tests passing for each agent
✅ Integration test passing for full flow
✅ End-to-end manual test successful
✅ Performance within targets (< 60s for 6 images)
✅ Code formatted, linted, and documented
✅ All changes committed and pushed

---

## Troubleshooting Common Issues

### Replicate API Errors
- Check API key is valid: test with simple prediction
- Monitor rate limits (check Replicate dashboard)
- Verify model IDs are correct and accessible
- Handle timeout errors (increase timeout if needed)

### WebSocket Not Receiving Updates
- Verify ws_manager is imported globally
- Check session_id matches between endpoint and WebSocket
- Test send_progress directly in Python shell
- Verify WebSocket connection is established before generation

### Image Generation Slow
- Check network connection to Replicate
- Verify parallel execution (asyncio.gather)
- Monitor Replicate API status page
- Consider using SDXL for faster testing

### Database Transaction Errors
- Check commit() is called after database operations
- Verify async session is used throughout
- Check for transaction conflicts
- Ensure proper error handling with rollback

---

## Next Steps

**Proceed to:** [Phase_3_Tasks.md](Phase_3_Tasks.md)

**What's Next:**
- Implement Video Generator Agent
- Implement scene planning with LLM
- Create Composition Layer with FFmpeg
- Build video generation endpoints
- Test complete video pipeline

---

## Notes & Observations

```
[Your notes here]
```

---

**Last Updated:** November 14, 2025
