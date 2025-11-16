# AI Educational Video Generator - Documentation Index

**Project:** AI Educational Video Generator MVP
**Version:** 3.0 (Educational Pivot - Implementation-Ready)
**Owner:** Nani Skinner — Technical Project Manager
**Sprint Duration:** 48 Hours
**Last Updated:** January 15, 2025

---

## Quick Start

**For Developers Starting Implementation:**
1. Read [01-executive-summary.md](./01-executive-summary.md) for project overview
2. Review [03-multi-agent-architecture.md](./03-multi-agent-architecture.md) for system design
3. Check [09-implementation-sequence.md](./09-implementation-sequence.md) for 48-hour sprint plan
4. Follow [10-testing-deployment.md](./10-testing-deployment.md) for deployment steps

**For Product/Design Teams:**
1. Start with [01-executive-summary.md](./01-executive-summary.md)
2. Deep dive into [02-user-journey-ui-specs.md](./02-user-journey-ui-specs.md)
3. Review cost structure in [08-cost-model-selection.md](./08-cost-model-selection.md)

**For Technical Architects:**
1. Begin with [03-multi-agent-architecture.md](./03-multi-agent-architecture.md)
2. Study [04-agent-specifications.md](./04-agent-specifications.md)
3. Review [05-data-models-database.md](./05-data-models-database.md)
4. Check [06-api-endpoints.md](./06-api-endpoints.md)

---

## Documentation Structure

### Core Documents (Read in Order)

| # | Document | Description | Audience | Est. Reading Time |
|---|----------|-------------|----------|-------------------|
| **01** | [Executive Summary](./01-executive-summary.md) | Project goals, scope, stack, costs | Everyone | 10 min |
| **02** | [User Journey & UI](./02-user-journey-ui-specs.md) | Screen-by-screen UI flows, teacher interactions | Designers, Frontend Devs | 20 min |
| **03** | [Multi-Agent Architecture](./03-multi-agent-architecture.md) | System diagram, agent responsibilities, data flow | Architects, Backend Devs | 15 min |
| **04** | [Agent Specifications](./04-agent-specifications.md) | Detailed specs for all 4 agents + Gemini | Backend Devs | 30 min |
| **05** | [Data Models & Database](./05-data-models-database.md) | Pydantic models, PostgreSQL schema | Backend Devs, DBAs | 15 min |
| **06** | [API Endpoints](./06-api-endpoints.md) | REST APIs, WebSocket, request/response formats | Frontend + Backend Devs | 15 min |
| **07** | [Frontend Components](./07-frontend-components.md) | Next.js components, hooks, utilities | Frontend Devs | 25 min |
| **08** | [Cost & Model Selection](./08-cost-model-selection.md) | Per-video costs, model rationale, optimization | Product, Engineering Leads | 15 min |
| **09** | [Implementation Sequence](./09-implementation-sequence.md) | 48-hour sprint plan, hourly breakdown | All Developers | 20 min |
| **10** | [Testing & Deployment](./10-testing-deployment.md) | Test strategies, deployment steps, success criteria | QA, DevOps, Developers | 20 min |

**Total Reading Time:** ~3 hours for complete understanding

---

## Document Relationships

```
01-executive-summary.md
    ├─ Defines: Project goals, scope, key decisions
    └─ References: All other documents

02-user-journey-ui-specs.md
    ├─ Implements: User-facing flows from 01
    ├─ Depends on: API endpoints (06), Frontend components (07)
    └─ Informs: Implementation sequence (09)

03-multi-agent-architecture.md
    ├─ Defines: System architecture, agent interactions
    ├─ References: Agent specs (04), Database (05), APIs (06)
    └─ Implements: Technical stack from 01

04-agent-specifications.md
    ├─ Implements: Agents from architecture (03)
    ├─ Depends on: Data models (05)
    └─ Informs: Implementation sequence (09)

05-data-models-database.md
    ├─ Supports: All agents (04), APIs (06)
    └─ Referenced by: Implementation sequence (09)

06-api-endpoints.md
    ├─ Implements: APIs from architecture (03)
    ├─ Connects: Frontend (02, 07) to Backend (04)
    └─ Uses: Data models (05)

07-frontend-components.md
    ├─ Implements: UI flows (02)
    ├─ Consumes: API endpoints (06)
    └─ Referenced by: Implementation sequence (09)

08-cost-model-selection.md
    ├─ Justifies: Technology choices from 01
    └─ Informs: Budget planning

09-implementation-sequence.md
    ├─ Synthesizes: All technical docs (03-07)
    ├─ Creates: 48-hour execution plan
    └─ References: Testing (10)

10-testing-deployment.md
    ├─ Validates: Implementation (09)
    ├─ Tests: All components (03-07)
    └─ Deploys: Complete system
```

---

## Key Concepts & Glossary

### Architecture Concepts

| Term | Definition | Document Reference |
|------|------------|-------------------|
| **Multi-Agent Architecture** | System using 4 specialized backend agents coordinated by orchestrator | [03](./03-multi-agent-architecture.md) |
| **Self-Healing Compositor** | Agent 5 that auto-corrects visual mismatches using LLM decisions | [04](./04-agent-specifications.md#agent-5) |
| **Hybrid Template + AI Pipeline** | Visual generation using hand-crafted templates + AI-generated variations | [01](./01-executive-summary.md#core-innovation) |
| **4-Criteria Gemini Rubric** | Validation on scientific accuracy, labels, age-appropriateness, clarity | [04](./04-agent-specifications.md#gemini-vision) |
| **Final Visual Approval Gate** | Last teacher decision point before automated composition | [02](./02-user-journey-ui-specs.md#screen-4) |

### Technical Terms

| Term | Definition | Document Reference |
|------|------------|-------------------|
| **Session** | Database record tracking one video generation from start to finish | [05](./05-data-models-database.md#sessions-table) |
| **Agent Input/Output** | Standardized interface for all backend agents | [04](./04-agent-specifications.md#agent-interface) |
| **WebSocket Progress** | Real-time updates sent to frontend during generation | [06](./06-api-endpoints.md#websocket) |
| **Text Slide Fallback** | Emergency educational slide when visual generation fails | [01](./01-executive-summary.md#text-slide-fallback) |
| **Template Library** | 10 hand-crafted scientifically-validated PSD files | [01](./01-executive-summary.md#mvp-scope) |

### Educational Terms

| Term | Definition | Document Reference |
|------|------------|-------------------|
| **4-Part Structure** | Hook → Concept → Process → Conclusion (60-second script format) | [02](./02-user-journey-ui-specs.md#screen-3) |
| **Confirmed Facts** | Teacher-validated key concepts, definitions, relationships | [02](./02-user-journey-ui-specs.md#screen-2) |
| **Reading Level** | Grade-appropriate language complexity (target: 6-7) | [01](./01-executive-summary.md#mvp-scope) |
| **Scientific Accuracy** | Factual correctness validated by Gemini AI | [01](./01-executive-summary.md#core-innovation) |

---

## Technology Stack Quick Reference

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS + shadcn/ui
- **Client-Side Processing:** PDF.js, URL fetching
- **Real-time:** WebSocket connection

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Validation:** Pydantic v2
- **Database:** PostgreSQL 15 + SQLAlchemy 2.0
- **Orchestration:** Python async/await

### AI/ML Services
- **LLM:** Replicate (Llama 3.1 70B Instruct)
- **Image Generation:** OpenAI (DALL-E 3)
- **Visual Validation:** Google Gemini 1.5 Pro Vision
- **TTS:** ElevenLabs + Play.ht (fallback)
- **Video Composition:** FFmpeg 6.0

### Deployment
- **Frontend:** Vercel
- **Backend:** Railway
- **Database:** Railway PostgreSQL
- **File Storage:** Temporary local (MVP)

---

## Cost Summary

| Component | Per-Video Cost | Notes |
|-----------|---------------|-------|
| Fact Extraction | $0.00 | Client-side (Next.js) |
| Script Generation | $0.01 | Llama 3.1 70B |
| Visual Generation | $0.16-$0.24 | Templates + DALL-E 3 |
| Gemini Validation | $3.60 | Largest cost, ensures quality |
| Audio (TTS) | $0.50 | Optional (ElevenLabs) |
| Self-Healing | $0-$0.08 | Emergency generation |
| **TOTAL** | **$4.28-$4.44** | Well under $15 target ✅ |

**MVP Development Budget:** $200 (covers 45+ test videos)

See [08-cost-model-selection.md](./08-cost-model-selection.md) for detailed breakdown.

---

## Success Criteria

### Functional Requirements
- ✅ End-to-end video generation in <5 minutes
- ✅ 60-second educational videos (1080p, 30fps)
- ✅ 100% scientific accuracy (Gemini validated)
- ✅ Teacher control at every stage
- ✅ Self-healing composition (never fails)
- ✅ Cost <$5 per video

### Performance Requirements
- Script generation: <10 seconds
- Visual generation: <70 seconds
- Gemini validation: <150 seconds
- Final composition: <120 seconds
- **Total:** <7 minutes end-to-end

See [10-testing-deployment.md](./10-testing-deployment.md) for complete criteria.

---

## Implementation Timeline

### Pre-Sprint (8-12 hours before)
- ✅ Create 10 scientific templates
- ✅ Validate with science teacher
- ✅ Upload to storage
- ✅ Populate database

### Day 1 (24 hours)
- **Hour 0-6:** Foundation + Script Generation
- **Hour 6-12:** Narrative Builder + Script UI
- **Hour 12-18:** Visual Pipeline Agent
- **Hour 18-24:** Visual Review + Gemini Foundation

### Day 2 (24 hours)
- **Hour 24-30:** Audio Pipeline
- **Hour 30-42:** Educational Compositor (Self-Healing)
- **Hour 42-46:** Final Output + Polish
- **Hour 46-48:** Testing + Deployment

See [09-implementation-sequence.md](./09-implementation-sequence.md) for hour-by-hour breakdown.

---

## Common Tasks & Where to Find Them

| Task | Document | Section |
|------|----------|---------|
| Implement login flow | [02-user-journey-ui-specs.md](./02-user-journey-ui-specs.md) | Screen 1 |
| Create script generation agent | [04-agent-specifications.md](./04-agent-specifications.md) | Agent 2 |
| Setup database schema | [05-data-models-database.md](./05-data-models-database.md) | Database Schema |
| Add API endpoint | [06-api-endpoints.md](./06-api-endpoints.md) | Content Generation |
| Build UI component | [07-frontend-components.md](./07-frontend-components.md) | Components |
| Optimize costs | [08-cost-model-selection.md](./08-cost-model-selection.md) | Cost Optimization |
| Deploy to production | [10-testing-deployment.md](./10-testing-deployment.md) | Deployment |
| Write tests | [10-testing-deployment.md](./10-testing-deployment.md) | Testing Strategy |

---

## FAQ

**Q: Where do I start if I'm new to the project?**
A: Read [01-executive-summary.md](./01-executive-summary.md) first, then based on your role:
- **Developer:** [09-implementation-sequence.md](./09-implementation-sequence.md)
- **Designer:** [02-user-journey-ui-specs.md](./02-user-journey-ui-specs.md)
- **Architect:** [03-multi-agent-architecture.md](./03-multi-agent-architecture.md)

**Q: How long is the sprint?**
A: 48 hours of focused development, plus 8-12 hours pre-sprint template preparation.

**Q: What if I can't find something in these docs?**
A: Check the [NewPRD.md](./NewPRD.md) original document, or contact the project owner.

**Q: Can I skip documents?**
A: Depends on your role. See "Quick Start" section above for recommended reading paths.

**Q: How do I track implementation progress?**
A: Follow the checklist in [09-implementation-sequence.md](./09-implementation-sequence.md).

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 3.0 | 2025-01-15 | Educational pivot, sharded documentation | Nani Skinner |
| 2.0 | 2025-01-10 | Multi-agent architecture redesign | Nani Skinner |
| 1.0 | 2025-01-05 | Initial MVP specification | Nani Skinner |

---

## Maintenance Notes

**Document Ownership:**
- **Owner:** Nani Skinner (Technical Project Manager)
- **Last Review:** January 15, 2025
- **Next Review:** Post-MVP (after 48-hour sprint)

**Update Process:**
1. Edit relevant document(s)
2. Update version number in document header
3. Update this index if structure changes
4. Notify team of significant changes

**Document Standards:**
- Use markdown format (.md)
- Include table of contents for docs >500 lines
- Cross-reference related documents
- Keep code examples up-to-date
- Version all documents consistently

---

**Status:** ✅ Ready for 48-Hour Sprint
**Last Updated:** January 15, 2025
