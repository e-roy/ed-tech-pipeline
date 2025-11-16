# API Endpoints

**Document:** 06 - API Endpoints
**Version:** 3.0
**Status:** 📝 To Be Extracted from NewPRD.md
**Last Updated:** January 15, 2025

---

## Document Purpose

This document contains complete REST API and WebSocket specifications for all backend endpoints.

## What Will Be Included

1. **Authentication Endpoints** - Login, session management
2. **Content Generation Endpoints** - Script, visuals, audio, video
3. **WebSocket Protocol** - Real-time progress updates
4. **Request/Response Examples** - Complete JSON samples
5. **Error Handling** - Error codes and messages
6. **Rate Limiting** - API limits and throttling

## Source Material

Extract from [NewPRD.md](./NewPRD.md):
- Lines 1571-1770: API Endpoints section
- POST /api/auth/login
- POST /api/sessions/create
- GET /api/sessions/{session_id}
- POST /api/generate-script
- POST /api/generate-visuals
- POST /api/approve-visuals-final
- POST /api/select-audio
- WS /ws/{session_id}

## Implementation Notes

For each endpoint include:
- Method and path
- Request body schema
- Response schema
- Success/error codes
- Example curl commands
- Authentication requirements

---

**Status:** Pending extraction from original PRD
**Priority:** High - Needed for Day 1 Hour 2-4
**Estimated Completion:** 45 minutes
