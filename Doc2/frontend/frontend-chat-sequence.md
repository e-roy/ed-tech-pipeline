# Frontend Chat Sequence Documentation

This document explains the sequence of messages in the chat panel and the corresponding sequences in the main content section during the educational video creation workflow.

## Overview

The create page (`/dashboard/create`) uses a two-panel layout:

- **Left Panel**: Chat interface for user interaction and AI responses
- **Right Panel**: Main content area showing facts, script review, and status

The chat and main content sections are synchronized through the `FactExtractionContext` and `ChatMessageContext` to provide a cohesive user experience.

## Complete Workflow Sequence

### Turn 1: Initial State

**Chat Panel:**

- **Assistant Message**: "I'll help you extract educational facts from your learning materials. Please provide:\n\n- Topic\n- Learning objective\n- Key points\n- PDF files or URLs (optional)\n\nI'll analyze the content and extract key facts for your review."

**Main Content:**

- **Step Indicator**: "Step 1: Extract facts from your learning materials"
- **Card**: "Ready to Extract Facts" with instructions:
  - Paste text directly into the chat
  - Upload a PDF file
  - Provide a URL to educational content

---

### Turn 2: User Submits Learning Materials

**Chat Panel:**

- **User Message**: User's input (text, PDF, or URL)
  - If PDF/URL: Shows file icon with "Learning materials processed"
  - Content is sent to AI for fact extraction

**Main Content:**

- **Loading State**: Card with spinner and "Analyzing your materials and extracting facts..."
- `isExtracting` state is set to `true`

---

### Turn 3: AI Processing (Streaming)

**Chat Panel:**

- **Assistant Message (Streaming)**: Shows `FactExtractionChainOfThought` component with progressive steps:
  1. "Reading materials" - Extracting text from PDFs and URLs (appears after 2s)
  2. "Analyzing content" - Processing with AI to understand key concepts (appears after 4.5s)
  3. "Identifying facts" - Extracting educational facts from materials (appears after 8s)
- Chain of thought is shown instead of streaming text during this turn

**Main Content:**

- Still shows loading spinner
- `isExtracting` remains `true`

---

### Turn 4: Facts Extracted

**Chat Panel:**

- **Assistant Message (Complete)**:
  - JSON code blocks are removed from display
  - Shows cleaned text response (if any)
  - Facts are parsed and stored in context

**Main Content:**

- **Step Indicator**: Still "Step 1: Extract facts from your learning materials"
- **FactExtractionPanel**:
  - Shows all extracted facts in editable cards
  - Each fact has:
    - Concept field (editable)
    - Details field (editable)
    - Delete button
  - "Add Fact" button
  - "Continue to Script Generation →" button
- `isExtracting` is set to `false`
- `extractedFacts` is populated

---

### Turn 5: User Reviews and Confirms Facts

**Chat Panel:**

- No new messages (user is reviewing facts in main panel)

**Main Content:**

- User can:
  - Edit fact concepts and details
  - Add new facts
  - Delete facts
  - Click "Continue to Script Generation →"

**When User Clicks Continue:**

- `confirmFacts()` is called
- `confirmedFacts` state is set
- Facts are stored in localStorage

---

### Turn 6: Facts Confirmed

**Chat Panel:**

- **User Message (Auto-generated)**: "These facts look good, let's proceed with script generation"
  - This message is automatically added when `confirmedFacts` changes from `null` to an array
  - Triggered by `useEffect` in `ChatPreview` component

**Main Content:**

- **Step Indicator**: "Step 2: Generate script (X facts ready)"
- **ScriptReviewPanel**:
  - Automatically triggers script generation via `useEffect`
  - Shows loading state: "Generating Script..." with spinner
  - Sets `isGeneratingScript` to `true`
- **Facts Confirmed Card**: Shows all confirmed facts in a read-only display

---

### Turn 7: Script Generation in Progress

**Chat Panel:**

- **Assistant Message (Auto-generated)**: Shows `ScriptGenerationChainOfThought` component with progressive steps:
  1. "Analyzing facts" - Reviewing confirmed educational facts and key concepts (appears after 2s)
  2. "Structuring narrative" - Organizing content into a coherent educational flow (appears after 4.5s)
  3. "Generating script segments" - Creating narration and visual guidance for each segment (appears after 8s)
- This appears when `isGeneratingScript` is `true` and `confirmedFacts` exists
- Chain of thought is shown as a separate assistant message

**Main Content:**

- **ScriptReviewPanel**:
  - Still shows "Generating Script..." loading state
  - `generateMutation.isPending` is `true`
  - Script generation API call is in progress

---

### Turn 8: Script Generated

**Chat Panel:**

- Chain of thought message remains visible (completed state)
- No new messages

**Main Content:**

- **Step Indicator**: "Step 2: Generate script (X facts ready)" or "Step 3: Review Script" if sessionId exists
- **ScriptReviewPanel**:
  - Shows script review interface with:
    - All script segments in editable cards
    - Each segment shows:
      - Segment number and type badge
      - Time range (start_time - end_time)
      - Narration textarea (editable)
      - Visual guidance textarea (editable)
      - Key concepts list
      - "Regenerate" button (placeholder for future feature)
  - "Approve Script & Generate Visuals →" button
  - `isGeneratingScript` is set to `false`
  - `generatedScript` state is populated

---

### Turn 9: User Reviews and Approves Script

**Chat Panel:**

- No new messages (user is reviewing script in main panel)

**Main Content:**

- User can:
  - Edit narration for each segment
  - Edit visual guidance for each segment
  - Click "Approve Script & Generate Visuals →"

**When User Clicks Approve:**

- `handleApprove()` is called
- `approveMutation.mutateAsync()` is executed
- Script is saved to database
- Session is created with `script_approved` status

---

### Turn 10: Script Approved

**Chat Panel:**

- **User Message (Auto-generated)**: "This script looks good, let's generate visuals"
  - This message is automatically added when script approval succeeds
  - Triggered by `onSuccess` callback in `approveMutation`
  - Note: Currently this may not appear if `ScriptReviewPanel` is outside `ChatMessageProvider` context

**Main Content:**

- **Step Indicator**: "Step 3: Review Script"
- Alert: "Script approved! Visual generation coming in next turn."
- `sessionId` is now available (from `getLatestSession` query)
- Ready for next turn (visual generation - not yet implemented)

---

## State Management

### Key Context States

**FactExtractionContext:**

- `extractedFacts`: Array of facts extracted from materials
- `isExtracting`: Boolean indicating fact extraction in progress
- `confirmedFacts`: Array of facts user has confirmed
- `isGeneratingScript`: Boolean indicating script generation in progress
- `sessionId`: ID of the current video generation session

**ChatMessageContext:**

- `sendMessage`: Function to programmatically add messages to chat
- Available within `ChatPreview` component tree

### State Transitions

```
Initial State
  ↓ (user submits materials)
isExtracting = true
  ↓ (AI processes)
Facts extracted → extractedFacts populated
  ↓ (user reviews)
User clicks Continue → confirmedFacts set
  ↓ (auto-triggered)
isGeneratingScript = true → Script generation starts
  ↓ (API completes)
Script generated → generatedScript populated
  ↓ (user reviews)
User clicks Approve → Session created, sessionId set
  ↓
Ready for next turn
```

---

## Component Responsibilities

### ChatPreview (`frontend/src/components/chat/chat-preview.tsx`)

- Manages chat state via `useChat` hook
- Provides `sendMessage` via `ChatMessageProvider`
- Detects fact confirmation and auto-adds user message
- Shows chain of thought components during processing
- Renders all chat messages

### ChatMessage (`frontend/src/components/chat/ChatMessage.tsx`)

- Renders individual chat messages
- Shows `FactExtractionChainOfThought` during fact extraction streaming
- Cleans up JSON code blocks from assistant messages
- Handles file attachments display

### CreatePage (`frontend/src/app/dashboard/create/page.tsx`)

- Main content area layout
- Conditionally renders:
  - Loading states
  - FactExtractionPanel
  - ScriptReviewPanel
  - Status cards
- Updates step indicator based on current state

### FactExtractionPanel (`frontend/src/components/fact-extraction/FactExtractionPanel.tsx`)

- Displays extracted facts in editable cards
- Allows user to add/edit/delete facts
- Triggers fact confirmation on "Continue" click

### ScriptReviewPanel (`frontend/src/components/generation/ScriptReviewPanel.tsx`)

- Automatically triggers script generation when facts are confirmed
- Shows loading state during generation
- Displays generated script segments for review
- Allows editing of narration and visual guidance
- Handles script approval and session creation
- Attempts to send approval message to chat (if context available)

---

## Message Flow Diagram

```
User Input
  ↓
Chat: User Message (with materials)
  ↓
Chat: Assistant Streaming → FactExtractionChainOfThought
  ↓
Main: Loading State
  ↓
Chat: Assistant Complete (facts extracted)
  ↓
Main: FactExtractionPanel (editable facts)
  ↓
User Clicks Continue
  ↓
Chat: User Message (auto) - "These facts look good..."
  ↓
Main: ScriptReviewPanel → Auto-triggers generation
  ↓
Chat: Assistant Message → ScriptGenerationChainOfThought
  ↓
Main: Loading State (generating script)
  ↓
Main: ScriptReviewPanel (editable script segments)
  ↓
User Clicks Approve
  ↓
Chat: User Message (auto) - "This script looks good..."
  ↓
Main: Session created, ready for next turn
```

---

## Chain of Thought Components

### FactExtractionChainOfThought

**Location**: `frontend/src/components/fact-extraction/FactExtractionChainOfThought.tsx`

**Steps** (progressive reveal):

1. Reading materials (2s delay)
2. Analyzing content (4.5s delay)
3. Identifying facts (8s delay)

**Shown when**: `isStreamingAssistant` is true during fact extraction

### ScriptGenerationChainOfThought

**Location**: `frontend/src/components/generation/ScriptGenerationChainOfThought.tsx`

**Steps** (progressive reveal):

1. Analyzing facts (2s delay)
2. Structuring narrative (4.5s delay)
3. Generating script segments (8s delay)

**Shown when**: `isGeneratingScript` is true and `confirmedFacts` exists

---

## Auto-Generated Messages

### When Facts Are Confirmed

- **Trigger**: `confirmedFacts` changes from `null` to array
- **Location**: `ChatPreview` useEffect hook
- **Message**: "These facts look good, let's proceed with script generation"
- **Role**: User

### When Script Is Approved

- **Trigger**: `approveMutation.onSuccess` callback
- **Location**: `ScriptReviewPanel` component
- **Message**: "This script looks good, let's generate visuals"
- **Role**: User
- **Note**: May not work if component is outside `ChatMessageProvider` context

---

## Error Handling

### Fact Extraction Errors

- Displayed in main content area as error card
- `extractionError` state is set
- Chat continues to function normally

### Script Generation Errors

- Logged to console
- `hasInitiatedGeneration` flag is reset to allow retry
- `isGeneratingScript` is set to `false`
- User can retry script generation

---

## Future Enhancements

1. **Script Approval Message**: Currently may not appear due to context limitations. Consider restructuring to ensure `ScriptReviewPanel` has access to `ChatMessageProvider`.

2. **Error Messages in Chat**: Currently errors are shown in main content. Could add error messages to chat for better visibility.

3. **Regenerate Segment**: Placeholder feature in `ScriptReviewPanel` - will allow regenerating individual script segments.

4. **Visual Generation Turn**: Next turn will add similar sequences for visual generation and review.

---

## Technical Notes

### Context Providers Hierarchy

```
DashboardLayout
  └─ ChatProvider
      └─ FactExtractionProvider
          └─ DashboardLayoutClient
              ├─ ChatPreview (wraps with ChatMessageProvider)
              │   └─ Chat messages
              └─ CreatePage
                  └─ ScriptReviewPanel (may not have ChatMessageProvider access)
```

### Key Files

- `frontend/src/components/chat/chat-preview.tsx` - Main chat component
- `frontend/src/components/chat/ChatMessage.tsx` - Individual message renderer
- `frontend/src/app/dashboard/create/page.tsx` - Main content area
- `frontend/src/components/fact-extraction/FactExtractionContext.tsx` - State management
- `frontend/src/components/chat/chat-message-context.tsx` - Chat message context
- `frontend/src/components/generation/ScriptReviewPanel.tsx` - Script review interface

---

## Summary

The chat and main content sections work together to provide a seamless workflow:

1. User submits materials via chat
2. AI processes and extracts facts (shown in chat with chain of thought)
3. Facts are displayed in main panel for review
4. User confirms facts → auto-message in chat
5. Script generation starts automatically (shown in chat with chain of thought)
6. Script is displayed in main panel for review
7. User approves script → auto-message in chat (if context available)
8. Ready for next turn

The synchronization is achieved through shared context (`FactExtractionContext`) and automatic message generation based on state changes.
