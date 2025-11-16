# AI Educational Video Generator - Documentation

**Version:** 3.0 (Educational Pivot - Implementation-Ready)
**Sprint:** 48 Hours
**Owner:** Nani Skinner
**Status:** ✅ Ready for Implementation

---

## 📖 About This Documentation

This folder contains the complete, sharded documentation for the AI Educational Video Generator MVP. The original monolithic PRD has been split into **11 focused documents** for easier navigation and implementation.

### Why Sharded?

- **Original PRD:** 4,379 lines, ~2.5 hours to read
- **Sharded Docs:** 11 documents, read only what you need
- **Benefit:** Faster onboarding, parallel work, better maintenance

---

## 🚀 Quick Start (Pick Your Path)

### For Developers (First Time)

**30-Minute Onboarding:**
1. Read [01-executive-summary.md](./01-executive-summary.md) (10 min)
2. Review [11-quick-reference-guide.md](./11-quick-reference-guide.md) (10 min)
3. Setup environment following quick reference (10 min)
4. Start implementing with [09-implementation-sequence.md](./09-implementation-sequence.md)

### For Product/Design Teams

**20-Minute Overview:**
1. Read [01-executive-summary.md](./01-executive-summary.md) (10 min)
2. Review [02-user-journey-ui-specs.md](./02-user-journey-ui-specs.md) (10 min)
3. Check cost structure in [08-cost-model-selection.md](./08-cost-model-selection.md) (optional)

### For Technical Architects

**45-Minute Deep Dive:**
1. Read [01-executive-summary.md](./01-executive-summary.md) (10 min)
2. Study [03-multi-agent-architecture.md](./03-multi-agent-architecture.md) (15 min)
3. Review [04-agent-specifications.md](./04-agent-specifications.md) (20 min)
4. Cross-reference with [05-data-models-database.md](./05-data-models-database.md) and [06-api-endpoints.md](./06-api-endpoints.md)

---

## 📁 Document Structure

### Core Documents (Read These First)

| Doc | File | Purpose | Est. Time |
|-----|------|---------|-----------|
| **00** | [INDEX.md](./00-INDEX.md) | Navigation guide, glossary, FAQ | 5 min |
| **01** | [01-executive-summary.md](./01-executive-summary.md) | Project goals, scope, stack, key decisions | 10 min |
| **02** | [02-user-journey-ui-specs.md](./02-user-journey-ui-specs.md) | Screen-by-screen UI flows | 20 min |
| **03** | [03-multi-agent-architecture.md](./03-multi-agent-architecture.md) | System architecture, agent responsibilities | 15 min |

### Implementation Guides

| Doc | File | Purpose | Est. Time |
|-----|------|---------|-----------|
| **04** | [04-agent-specifications.md](./04-agent-specifications.md) | Detailed agent specs (pending) | 30 min |
| **05** | [05-data-models-database.md](./05-data-models-database.md) | Database schema, Pydantic models (pending) | 15 min |
| **06** | [06-api-endpoints.md](./06-api-endpoints.md) | REST APIs, WebSocket specs (pending) | 15 min |
| **07** | [07-frontend-components.md](./07-frontend-components.md) | Next.js components, hooks (pending) | 25 min |

### Planning & Execution

| Doc | File | Purpose | Est. Time |
|-----|------|---------|-----------|
| **08** | [08-cost-model-selection.md](./08-cost-model-selection.md) | Cost breakdown, model selection (pending) | 15 min |
| **09** | [09-implementation-sequence.md](./09-implementation-sequence.md) | 48-hour sprint plan (pending) | 20 min |
| **10** | [10-testing-deployment.md](./10-testing-deployment.md) | Testing strategy, deployment steps (pending) | 20 min |
| **11** | [11-quick-reference-guide.md](./11-quick-reference-guide.md) | Developer cheat sheet, code snippets | 10 min |

### Original Document

| Doc | File | Purpose |
|-----|------|---------|
| **Original** | [NewPRD.md](./NewPRD.md) | Complete monolithic PRD (4,379 lines) - Reference only |

---

## 🎯 What Are We Building?

**AI-Powered Educational Video Generator** that creates 60-second middle school science videos with:

- ✅ **Scientific accuracy** validated by Gemini Vision AI (4-criteria rubric)
- ✅ **Teacher control** at every stage (fact confirmation, script editing, visual approval)
- ✅ **Professional quality** (1080p, age-appropriate narration, clear diagrams)
- ✅ **Cost efficiency** (target $4-5 per video, well under $15 budget)
- ✅ **Self-healing intelligence** (auto-corrects mismatches, text slide fallback)

### Core Innovation

**Hybrid Template + AI Pipeline with Self-Healing Validation**

1. **10 hand-crafted templates** (5 topics × 2 variations) for guaranteed accuracy
2. **AI fills gaps** with custom visuals when templates don't fit
3. **Gemini analyzes every frame** (30fps, 4-criteria scientific validation)
4. **Ed Compositor self-heals** mismatches using LLM-powered decisions
5. **Never fails** - falls back to educational text slides if visual generation fails

---

## 🏗️ Architecture Overview

```
Next.js Frontend (Fact Extraction + UI)
    ↓ REST API + WebSocket
FastAPI Backend (Orchestrator)
    ↓ Coordinates 4 Agents
┌────────────────────────────────────────┐
│ Agent 2: Narrative Builder (Llama 3.1) │
│ Agent 3: Visual Pipeline (Templates+AI)│
│ Agent 4: Audio Pipeline (TTS)          │
│ Agent 5: Ed Compositor (Self-Healing)  │
└────────────────────────────────────────┘
    ↓ Calls External Services
┌────────────────────────────────────────┐
│ DALL-E 3, Gemini Vision, ElevenLabs    │
│ FFmpeg, PostgreSQL                      │
└────────────────────────────────────────┘
```

**Key Architectural Decisions:**
- **Next.js does fact extraction** (no backend Agent 1) → Better UX
- **Gemini runs AFTER teacher approval** → Faster visual review
- **Text slide fallback** → Never shows incorrect content
- **Direct async calls** (not message queue) → Simpler MVP

See [03-multi-agent-architecture.md](./03-multi-agent-architecture.md) for details.

---

## 💰 Cost Structure

| Component | Per-Video Cost | Notes |
|-----------|---------------|-------|
| Fact Extraction | $0.00 | Client-side (Next.js) |
| Script Generation | $0.01 | Llama 3.1 70B |
| Visual Generation | $0.20 | Templates + DALL-E 3 |
| Gemini Validation | $3.60 | 30fps frame analysis |
| Audio (TTS) | $0.50 | ElevenLabs |
| Self-Healing | $0-$0.08 | Emergency generation |
| **TOTAL** | **$4.28-$4.44** | ✅ Under $15 target |

**MVP Budget:** $200 for testing (covers 45+ test videos)

See [08-cost-model-selection.md](./08-cost-model-selection.md) for optimization strategies.

---

## ⏱️ Implementation Timeline

### Pre-Sprint (8-12 hours)
- Create 10 scientific templates
- Validate with science teacher
- Upload to storage

### Day 1 (24 hours)
- **Hours 0-6:** Foundation + Script Generation
- **Hours 6-12:** Narrative Builder Agent + UI
- **Hours 12-18:** Visual Pipeline Agent
- **Hours 18-24:** Visual Review UI + Gemini Foundation

### Day 2 (24 hours)
- **Hours 24-30:** Audio Pipeline
- **Hours 30-42:** Educational Compositor (Self-Healing)
- **Hours 42-46:** Final Output + Polish
- **Hours 46-48:** Testing + Deployment

**Total:** 48 hours focused development

See [09-implementation-sequence.md](./09-implementation-sequence.md) for hour-by-hour breakdown.

---

## 🛠️ Technology Stack

### Frontend
- Next.js 14 (App Router)
- TypeScript + Tailwind CSS
- PDF.js (client-side fact extraction)
- WebSocket (real-time progress)

### Backend
- FastAPI (Python 3.11+)
- PostgreSQL 15 + SQLAlchemy 2.0
- Pydantic v2 (validation)
- Python async/await (orchestration)

### AI/ML Services
- **LLM:** Replicate (Llama 3.1 70B Instruct)
- **Images:** OpenAI (DALL-E 3)
- **Validation:** Google Gemini 1.5 Pro Vision
- **TTS:** ElevenLabs
- **Video:** FFmpeg 6.0

### Deployment
- Frontend: Vercel
- Backend: Railway
- Database: Railway PostgreSQL

---

## 📋 Success Criteria

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

## 🚦 Current Status

| Component | Status | Document |
|-----------|--------|----------|
| Executive Summary | ✅ Complete | [01](./01-executive-summary.md) |
| User Journey & UI | ✅ Complete | [02](./02-user-journey-ui-specs.md) |
| Architecture | ✅ Complete | [03](./03-multi-agent-architecture.md) |
| Index & Navigation | ✅ Complete | [00](./00-INDEX.md) |
| Quick Reference | ✅ Complete | [11](./11-quick-reference-guide.md) |
| Agent Specifications | ⏳ Pending | [04](./04-agent-specifications.md) |
| Database Schema | ⏳ Pending | [05](./05-data-models-database.md) |
| API Endpoints | ⏳ Pending | [06](./06-api-endpoints.md) |
| Frontend Components | ⏳ Pending | [07](./07-frontend-components.md) |
| Cost & Model Selection | ⏳ Pending | [08](./08-cost-model-selection.md) |
| Implementation Sequence | ⏳ Pending | [09](./09-implementation-sequence.md) |
| Testing & Deployment | ⏳ Pending | [10](./10-testing-deployment.md) |

**Next Steps:**
1. Complete remaining documentation shards (04-10)
2. Review all documents with team
3. Execute pre-sprint template preparation
4. Begin 48-hour implementation sprint

---

## 🤝 How to Contribute

### Adding New Documentation

1. Create new markdown file in Doc2/
2. Follow naming convention: `##-descriptive-name.md`
3. Include header with document metadata
4. Update [00-INDEX.md](./00-INDEX.md) with new entry
5. Cross-reference related documents

### Updating Existing Documents

1. Edit the relevant .md file
2. Update version number in header
3. Update "Last Updated" date
4. If significant changes, notify team
5. Update [README.md](./README.md) if needed

### Document Standards

- Use markdown format (.md)
- Include table of contents for docs >500 lines
- Add code examples where helpful
- Cross-reference related documents
- Keep consistent formatting

---

## 📞 Support & Contact

**Project Owner:** Nani Skinner (Technical Project Manager)

**Questions?**
- Check [00-INDEX.md](./00-INDEX.md) FAQ section
- Review [11-quick-reference-guide.md](./11-quick-reference-guide.md) for common issues
- Consult original [NewPRD.md](./NewPRD.md) for comprehensive details

**Found an Issue?**
- Open issue with specific document reference
- Include section number and suggested fix
- Propose alternative wording if applicable

---

## 📊 Documentation Metrics

- **Total Documents:** 11 sharded + 1 original + README
- **Total Lines:** ~4,400 (original) + ~2,500 (sharded) = ~6,900 lines
- **Avg Reading Time per Doc:** 15 minutes
- **Complete Onboarding Time:** 30 min (quick) to 3 hours (comprehensive)
- **Implementation Ready:** ✅ Yes

---

## 🎓 Learning Path

**For Complete Beginners:**
1. Read README.md (this file) - 10 min
2. Read [01-executive-summary.md](./01-executive-summary.md) - 10 min
3. Review [11-quick-reference-guide.md](./11-quick-reference-guide.md) - 10 min
4. Setup development environment - 20 min
5. Follow [02-user-journey-ui-specs.md](./02-user-journey-ui-specs.md) for UI flow understanding

**For Experienced Developers:**
1. Skim README.md - 5 min
2. Read [03-multi-agent-architecture.md](./03-multi-agent-architecture.md) - 15 min
3. Jump to [09-implementation-sequence.md](./09-implementation-sequence.md) - 10 min
4. Reference other docs as needed during implementation

**For Reviewers/Stakeholders:**
1. Read [01-executive-summary.md](./01-executive-summary.md) - 10 min
2. Review cost structure in [08-cost-model-selection.md](./08-cost-model-selection.md) - 10 min
3. Check success criteria in [10-testing-deployment.md](./10-testing-deployment.md) - 10 min

---

## 📝 Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 3.0 | 2025-01-15 | Sharded documentation, educational pivot | Nani Skinner |
| 2.0 | 2025-01-10 | Multi-agent architecture redesign | Nani Skinner |
| 1.0 | 2025-01-05 | Initial MVP specification | Nani Skinner |

---

## 🎉 Ready to Build?

**Start Here:**
1. Review [11-quick-reference-guide.md](./11-quick-reference-guide.md)
2. Setup your environment
3. Choose your implementation task from [09-implementation-sequence.md](./09-implementation-sequence.md)
4. Build amazing educational videos! 🚀

---

**Last Updated:** January 15, 2025
**Status:** ✅ Ready for 48-Hour Sprint
**License:** [Your License]
**Owner:** Nani Skinner
