# Phase 00: Pre-Sprint Template Preparation

**Timeline:** 8-12 hours before Day 1 sprint begins
**Dependencies:** None (must complete BEFORE sprint)
**Completion:** 0% (0/20 tasks complete)

---

## Overview

This phase MUST be completed before the 48-hour sprint begins. All 10 educational templates need to be created, scientifically validated, and uploaded to cloud storage with metadata entries in the database.

---

## Tasks

### 1. Template Generation (4-6 hours)

#### 1.1 Set Up Template Generation Environment
- [ ] Install template generation tools (Photoshop/GIMP or Python PIL)
- [ ] Set up DALL-E 3 API access for AI-assisted generation
- [ ] Create template specification document (dimensions, layers, style guide)
- [ ] Set up version control for template files

**Dependencies:** None
**Testing:** Run tool and verify it can create/save image files

#### 1.2 Generate Base Template 1: Solar System
- [ ] Create 1920x1080 canvas
- [ ] Add background layer (space theme)
- [ ] Add planet positions layer
- [ ] Add label layer (editable text)
- [ ] Add title layer
- [ ] Save as PSD with named layers
- [ ] Export preview PNG

**Dependencies:** Task 1.1
**Testing:** Open PSD, verify all layers are editable and properly named

#### 1.3 Generate Base Template 2: Photosynthesis
- [ ] Create 1920x1080 canvas
- [ ] Add plant illustration layer
- [ ] Add chloroplast detail layer
- [ ] Add arrow/process flow layer
- [ ] Add label layer (chemical formulas)
- [ ] Save as PSD with named layers
- [ ] Export preview PNG

**Dependencies:** Task 1.1
**Testing:** Open PSD, verify layers can be shown/hidden independently

#### 1.4 Generate Base Template 3: Water Cycle
- [ ] Create 1920x1080 canvas
- [ ] Add landscape background (ocean, clouds, mountains)
- [ ] Add water state layers (liquid, vapor, ice)
- [ ] Add arrow/flow indicators
- [ ] Add label layer (evaporation, condensation, precipitation)
- [ ] Save as PSD with named layers
- [ ] Export preview PNG

**Dependencies:** Task 1.1
**Testing:** Verify labels can be edited without affecting background

#### 1.5 Generate Base Template 4: Cell Structure
- [ ] Create 1920x1080 canvas
- [ ] Add cell membrane layer
- [ ] Add organelle layers (nucleus, mitochondria, etc.)
- [ ] Add label callout layer
- [ ] Save as PSD with named layers
- [ ] Export preview PNG

**Dependencies:** Task 1.1
**Testing:** Verify organelles are on separate layers

#### 1.6 Generate Base Template 5: Food Chain
- [ ] Create 1920x1080 canvas
- [ ] Add ecosystem background
- [ ] Add organism layers (plants, herbivores, carnivores)
- [ ] Add energy flow arrows
- [ ] Add label layer
- [ ] Save as PSD with named layers
- [ ] Export preview PNG

**Dependencies:** Task 1.1
**Testing:** Verify arrow direction can be adjusted

#### 1.7 Generate Templates 6-10
- [ ] Template 6: Human Body Systems (1920x1080 PSD)
- [ ] Template 7: Rock Cycle (1920x1080 PSD)
- [ ] Template 8: Periodic Table Element (1920x1080 PSD)
- [ ] Template 9: Math Equations/Graphs (1920x1080 PSD)
- [ ] Template 10: Historical Timeline (1920x1080 PSD)
- [ ] Export preview PNGs for all

**Dependencies:** Task 1.1
**Testing:** Open each PSD, verify editable layers exist

---

### 2. Scientific Validation (2-3 hours)

#### 2.1 Review Template Accuracy
- [ ] Solar System: Verify planet order, relative sizes, colors
- [ ] Photosynthesis: Verify chemical formula (6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂)
- [ ] Water Cycle: Verify process flow accuracy
- [ ] Cell Structure: Verify organelle placement and names
- [ ] Food Chain: Verify trophic level accuracy
- [ ] Templates 6-10: Review scientific accuracy

**Dependencies:** Tasks 1.2-1.7
**Testing:** Cross-reference with science textbooks or educational resources

#### 2.2 Age-Appropriateness Check (Grades 6-7)
- [ ] Verify vocabulary is appropriate (no overly technical jargon)
- [ ] Check visual complexity (not too simple, not too complex)
- [ ] Verify reading level of labels
- [ ] Confirm alignment with middle school standards

**Dependencies:** Task 2.1
**Testing:** Ask target audience (or educator) to review

#### 2.3 Make Corrections Based on Validation
- [ ] Update any scientifically inaccurate elements
- [ ] Simplify overly complex vocabulary
- [ ] Re-export corrected PSDs and PNGs
- [ ] Document changes made

**Dependencies:** Tasks 2.1, 2.2
**Testing:** Re-review with validator to confirm fixes

---

### 3. Layer Preparation (2-3 hours)

#### 3.1 Standardize Layer Structure
- [ ] Create layer naming convention document
- [ ] Ensure all templates have consistent layer names:
  - `background`
  - `main_content`
  - `labels`
  - `title`
  - `subtitle` (if applicable)
- [ ] Group related layers in folders

**Dependencies:** Tasks 1.2-1.7, 2.3
**Testing:** Write script to parse PSD layers, verify naming convention

#### 3.2 Create Layer Metadata
- [ ] For each template, document editable layers in JSON:
  ```json
  {
    "template_id": "solar_system_01",
    "editable_layers": ["labels", "title"],
    "customization_options": ["planet_labels", "title_text"]
  }
  ```
- [ ] Create metadata.json for all 10 templates

**Dependencies:** Task 3.1
**Testing:** Validate JSON syntax, ensure all layers are documented

#### 3.3 Test Layer Customization
- [ ] Write Python script using PIL/Pillow to:
  - Open PSD
  - Modify text layer
  - Export as PNG
- [ ] Test on 2-3 templates
- [ ] Verify exported PNG reflects changes

**Dependencies:** Task 3.2
**Testing:** Run script, compare before/after PNGs

---

### 4. Cloud Storage Upload (30 minutes)

#### 4.1 Set Up Cloud Storage
- [ ] Choose storage provider (S3, Cloudflare R2, or Firebase Storage)
- [ ] Create bucket/container named `educational-templates`
- [ ] Set up public read access (or signed URLs)
- [ ] Configure CORS for frontend access

**Dependencies:** None
**Testing:** Upload test file, verify accessible via public URL

#### 4.2 Upload Template Files
- [ ] Upload all 10 PSD files to `templates/psd/` folder
- [ ] Upload all 10 preview PNG files to `templates/previews/` folder
- [ ] Record URLs for each file
- [ ] Verify file integrity (checksums or file size)

**Dependencies:** Tasks 1.2-1.7, 2.3, 4.1
**Testing:** Download 2-3 files from URLs, verify they match originals

---

### 5. Database Metadata (30 minutes)

#### 5.1 Create Templates Table
- [ ] Connect to Railway PostgreSQL database
- [ ] Create `templates` table with schema:
  ```sql
  CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    template_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    psd_url TEXT NOT NULL,
    preview_url TEXT NOT NULL,
    editable_layers JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
  );
  ```
- [ ] Verify table created successfully

**Dependencies:** Task 4.2
**Testing:** Run `\d templates` in psql to view schema

#### 5.2 Insert Template Records
- [ ] Insert record for each template:
  ```sql
  INSERT INTO templates (template_id, name, category, psd_url, preview_url, editable_layers)
  VALUES (
    'solar_system_01',
    'Solar System Overview',
    'astronomy',
    'https://storage.../templates/psd/solar_system.psd',
    'https://storage.../templates/previews/solar_system.png',
    '{"labels": true, "title": true}'::jsonb
  );
  ```
- [ ] Insert all 10 records
- [ ] Verify insert count: `SELECT COUNT(*) FROM templates;` (should be 10)

**Dependencies:** Tasks 3.2, 4.2, 5.1
**Testing:** Query database, verify all 10 records exist with correct URLs

#### 5.3 Create Template Library JSON
- [ ] Create `template_library.json` file with all template metadata
- [ ] Structure:
  ```json
  {
    "templates": [
      {
        "id": "solar_system_01",
        "name": "Solar System Overview",
        "category": "astronomy",
        "preview_url": "...",
        "tags": ["space", "planets", "solar system"]
      }
    ]
  }
  ```
- [ ] Save to project repository

**Dependencies:** Task 5.2
**Testing:** Validate JSON syntax, ensure all 10 templates included

---

## Pre-Sprint Checklist

**Before starting Day 1, verify:**

- [ ] All 10 templates created and saved as PSD
- [ ] All templates scientifically validated
- [ ] All templates uploaded to cloud storage
- [ ] All template URLs publicly accessible
- [ ] Database `templates` table populated with 10 records
- [ ] Template metadata JSON created
- [ ] Preview images generated for all templates
- [ ] Layer customization tested on at least 2 templates
- [ ] Template library JSON saved to repository
- [ ] All URLs tested and working

**If any checkbox is unchecked, DO NOT start the sprint. Complete remaining tasks first.**

---

## Completion Status

**Total Tasks:** 20
**Completed:** 0
**Percentage:** 0%

**Status:** ⏳ Not Started

---

## Notes

- Template quality is critical - these will be used for 60%+ of all visuals
- Scientific accuracy must be verified by subject matter expert
- Test layer customization thoroughly to avoid issues during sprint
- Keep backup copies of all PSD files locally
