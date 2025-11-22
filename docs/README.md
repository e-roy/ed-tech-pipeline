# Documentation Directory

This directory contains all project documentation organized by category.

## Directory Structure

```
docs/
├── archive/                    # Historical/outdated documentation
├── agents/                     # Agent-specific documentation
├── architecture/               # Architecture diagrams and specifications
├── backend/                   # Backend-specific guides and documentation
├── frontend/                   # Frontend-specific documentation
├── implementation-plans/       # Implementation planning documents
├── remotion/                   # Remotion video composition docs
├── resources/                  # Reference materials (style prompts, etc.)
└── tasks/                      # Implementation task breakdowns
```

## Main Documentation

The primary project documentation is located in:

- **Root level:**
  - `README.md` - Main project README
  - `ARCHITECTURE.md` - System architecture document
  - `prd.md` - Product Requirements Document

- **Doc2/ directory:**
  - `00-INDEX.md` through `11-quick-reference-guide.md` - Sharded documentation
  - `NewPRD.md` - Original monolithic PRD (reference)

## Quick Navigation

### For Developers
- Start with: `Doc2/01-executive-summary.md`
- Architecture: `docs/architecture/` or `ARCHITECTURE.md`
- Implementation tasks: `docs/tasks/`
- Agent docs: `docs/agents/`

### For Backend Developers
- Backend README: `backend/README.md`
- Backend guides: `docs/backend/`
- Agent documentation: `docs/agents/`
- API documentation: `backend/API.md`

### For Frontend Developers
- Frontend README: `frontend/README.md`
- Frontend docs: `docs/frontend/`
- Component specs: `Doc2/07-frontend-components.md`

### For Architects
- System architecture: `ARCHITECTURE.md`
- Detailed architecture: `docs/architecture/`
- Multi-agent architecture: `Doc2/03-multi-agent-architecture.md`

## Archive

The `archive/` directory contains historical documentation that may be outdated but kept for reference:
- Old planning documents (*.plan.md)
- Integration success reports
- Quick start guides for completed features
- Historical summaries

## Resources

The `resources/` directory contains reference materials:
- Style prompts for AI generation
- Other reusable reference documents

## Maintenance

When adding new documentation:
1. Place it in the appropriate category directory
2. Update this README if adding a new category
3. Cross-reference from main documentation (Doc2/ or root level)
4. Archive outdated docs rather than deleting them

