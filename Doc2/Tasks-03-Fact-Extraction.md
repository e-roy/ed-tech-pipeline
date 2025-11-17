# Phase 03: Fact Extraction (Next.js) (Hours 4-6)

**Timeline:** Day 1, Hours 4-6
**Dependencies:** Phase 02 (Auth & Session Management)
**Completion:** ~69% (18/26 tasks complete)

---

## Overview

Implement client-side fact extraction from PDF files, URLs, and text input. This Next.js-based extraction reduces backend costs by processing documents in the browser.

---

## Tasks

### 1. PDF Extraction Setup

#### 1.1 Install PDF.js Library

- [x] Install pdf.js: `npm install pdfjs-dist` (installed via bun)
- [x] Create `frontend/lib/pdfWorker.ts`:

  ```typescript
  // Dynamic import for client-side only
  export async function getPdfjsLib() {
    if (typeof window === "undefined") {
      throw new Error("PDF.js can only be used in the browser");
    }

    const pdfjsLib = await import("pdfjs-dist");

    // Use the worker from the public folder (copied during build)
    // This is more reliable than CDN and works with Next.js
    pdfjsLib.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

    return pdfjsLib;
  }
  ```

  **Note:** Uses dynamic imports to avoid SSR issues. Worker file copied to public folder via postinstall script.

**Dependencies:** Phase 02 complete
**Testing:** Import: `import { getPdfjsLib } from '@/lib/pdfWorker'`

#### 1.2 Create PDF Text Extraction Function

- [x] Create `frontend/lib/extractPDF.ts`:

  ```typescript
  import { getPdfjsLib } from "./pdfWorker";

  export async function extractTextFromPDF(file: File): Promise<string> {
    const pdfjsLib = await getPdfjsLib();
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

    let fullText = "";

    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
      const page = await pdf.getPage(pageNum);
      const textContent = await page.getTextContent();
      const pageText = textContent.items
        .map((item) => {
          // Type guard for text items
          if ("str" in item) {
            return item.str;
          }
          return "";
        })
        .join(" ");
      fullText += pageText + "\n";
    }

    return fullText;
  }
  ```

  **Note:** Uses type guards for better TypeScript safety.

**Dependencies:** Task 1.1
**Testing:** Test with sample PDF file (tested in actual flow via chat component)

#### 1.3 Test PDF Extraction

- [ ] Create test component `frontend/components/TestPDFExtraction.tsx` (not created - functionality tested in actual flow)
- [x] Upload a test PDF (tested via chat component)
- [x] Verify text extraction works (verified in production flow)

**Dependencies:** Task 1.2
**Testing:** PDF extraction tested and working in chat component on `/dashboard/create` page

---

### 2. Fact Extraction Logic

#### 2.1 Create Concept Detection Function

- [ ] Create `frontend/lib/extractFacts.ts` with keyword-based extraction
      **Note:** This approach was replaced with AI agent-based extraction. See section 2.3.

**Dependencies:** None (pure function)
**Status:** Not implemented - replaced with AI agent approach

#### 2.2 Test Fact Extraction

- [ ] Test keyword-based fact extraction
      **Note:** Not applicable - using AI agent instead

**Dependencies:** Task 2.1
**Status:** Not applicable

#### 2.3 AI Agent-Based Fact Extraction

- [x] Create chat API route (`frontend/src/app/api/chat/route.ts`) with system message instructing AI to extract facts
- [x] Implement JSON parsing from AI responses in `chat-preview.tsx`
- [x] Define Fact interface in `frontend/src/types/index.ts`:
  ```typescript
  export interface Fact {
    concept: string;
    details: string;
    confidence: number;
  }
  ```
- [x] Parse JSON facts from AI response using regex pattern matching
- [x] Update FactExtractionContext when facts are extracted

**Dependencies:** Phase 02 (Auth & Session Management)
**Implementation:** AI agent extracts 5-15 educational facts from materials and returns them in structured JSON format. Facts are parsed from AI responses and displayed in FactExtractionPanel.

---

### 3. Topic Input Page

#### 3.1 Create Topic Input Component

- [ ] Create `frontend/app/session/[id]/topic-input/page.tsx`:
      **Note:** This separate page was not created. Instead, fact extraction was integrated into the existing `/dashboard/create` page using the `chat-preview.tsx` component. See sections 3.3-3.5 for actual implementation.

  ```typescript
  "use client";
  import { useState } from "react";
  import { useParams, useRouter } from "next/navigation";
  import { extractTextFromPDF } from "@/lib/extractPDF";
  import { extractFacts, Fact } from "@/lib/extractFacts";

  export default function TopicInputPage() {
    const params = useParams();
    const router = useRouter();
    const sessionId = params.id;

    const [inputMethod, setInputMethod] = useState<"text" | "pdf" | "url">(
      "text"
    );
    const [textInput, setTextInput] = useState("");
    const [urlInput, setUrlInput] = useState("");
    const [extractedFacts, setExtractedFacts] = useState<Fact[]>([]);
    const [loading, setLoading] = useState(false);

    const handlePDFUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      setLoading(true);
      try {
        const text = await extractTextFromPDF(file);
        const facts = extractFacts(text);
        setExtractedFacts(facts);
      } catch (error) {
        console.error("PDF extraction error:", error);
        alert("Failed to extract text from PDF");
      } finally {
        setLoading(false);
      }
    };

    const handleTextSubmit = () => {
      setLoading(true);
      const facts = extractFacts(textInput);
      setExtractedFacts(facts);
      setLoading(false);
    };

    const handleContinue = () => {
      // Store facts in localStorage for now (will use API later)
      localStorage.setItem(
        `facts_${sessionId}`,
        JSON.stringify(extractedFacts)
      );
      router.push(`/session/${sessionId}/script-review`);
    };

    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <h1 className="text-3xl font-bold mb-6">Input Learning Material</h1>
        <p className="text-gray-600 mb-6">Session ID: {sessionId}</p>

        {/* Input method selector */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setInputMethod("text")}
            className={`px-4 py-2 rounded ${
              inputMethod === "text" ? "bg-blue-600 text-white" : "bg-white"
            }`}
          >
            Text Input
          </button>
          <button
            onClick={() => setInputMethod("pdf")}
            className={`px-4 py-2 rounded ${
              inputMethod === "pdf" ? "bg-blue-600 text-white" : "bg-white"
            }`}
          >
            Upload PDF
          </button>
          <button
            onClick={() => setInputMethod("url")}
            className={`px-4 py-2 rounded ${
              inputMethod === "url" ? "bg-blue-600 text-white" : "bg-white"
            }`}
          >
            URL
          </button>
        </div>

        {/* Input forms */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          {inputMethod === "text" && (
            <div>
              <label className="block text-sm font-medium mb-2">
                Paste your text here:
              </label>
              <textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                className="w-full border rounded px-3 py-2 h-48"
                placeholder="Paste educational content here..."
              />
              <button
                onClick={handleTextSubmit}
                className="mt-4 bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
              >
                Extract Facts
              </button>
            </div>
          )}

          {inputMethod === "pdf" && (
            <div>
              <label className="block text-sm font-medium mb-2">
                Upload PDF file:
              </label>
              <input
                type="file"
                accept=".pdf"
                onChange={handlePDFUpload}
                className="block"
              />
            </div>
          )}

          {inputMethod === "url" && (
            <div>
              <label className="block text-sm font-medium mb-2">
                Enter URL:
              </label>
              <input
                type="url"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                className="w-full border rounded px-3 py-2"
                placeholder="https://..."
              />
              <p className="text-sm text-gray-500 mt-2">
                URL extraction coming soon
              </p>
            </div>
          )}
        </div>

        {/* Extracted facts */}
        {loading && <div>Extracting facts...</div>}

        {extractedFacts.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-bold mb-4">
              Extracted Facts ({extractedFacts.length})
            </h2>
            <div className="space-y-3">
              {extractedFacts.map((fact, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-4">
                  <div className="font-semibold">{fact.concept}</div>
                  <div className="text-sm text-gray-600">{fact.details}</div>
                </div>
              ))}
            </div>

            <button
              onClick={handleContinue}
              className="mt-6 bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700"
            >
              Continue to Script Generation →
            </button>
          </div>
        )}
      </div>
    );
  }
  ```

**Dependencies:** Tasks 1.2, 2.1
**Testing:** Navigate to page, test all 3 input methods

#### 3.2 Update Dashboard to Navigate to Topic Input

- [ ] Update `frontend/app/dashboard/page.tsx`:
  ```typescript
  const handleSessionCreated = (sessionId: number) => {
    router.push(`/session/${sessionId}/topic-input`);
  };
  ```

**Dependencies:** Task 3.1
**Testing:** Create session, should redirect to topic input page

---

### 4. URL Fetching (Optional Enhancement)

#### 4.1 Create URL Fetch Function

- [x] Create `frontend/lib/fetchURL.ts`:

  ```typescript
  export async function fetchURLContent(url: string): Promise<string> {
    // Try multiple CORS proxies for better reliability
    const proxies = [
      "https://api.allorigins.win/get?url=",
      "https://corsproxy.io/?",
      "https://api.codetabs.com/v1/proxy?quest=",
    ];

    // Attempts each proxy with timeout and error handling
    // Strips HTML tags and returns text content
  }
  ```

  **Note:** Enhanced with multiple proxy fallbacks, 10-second timeout, and better error handling for QUIC protocol errors.

**Dependencies:** None
**Testing:** Tested with public URLs via chat component

#### 4.2 Add URL Fetching to Topic Input

- [x] URL fetching integrated into `chat-preview.tsx`:
  - Automatically detects URLs in user messages
  - Fetches content using CORS proxy before sending to AI
  - Content is included in AI prompt but hidden from chat display

**Dependencies:** Tasks 3.5, 4.1
**Testing:** URL content successfully fetched and processed via chat component

---

### 5. Fact Review & Editing

#### 5.1 Make Facts Editable

- [x] Facts are editable in `FactExtractionPanel.tsx`:
  - Uses `Input` component for concept editing
  - Uses `Textarea` component for details editing
  - Updates are reflected immediately in the panel
  - Facts are stored in FactExtractionContext

**Dependencies:** Task 3.4
**Testing:** Facts can be edited inline in the FactExtractionPanel

#### 5.2 Add Fact Management Actions

- [x] Delete button implemented in `FactExtractionPanel.tsx`:
  - Each fact has a delete button (Trash2 icon)
  - Removes fact from the list immediately
- [x] Add Fact button implemented:
  - "Add Fact" button with Plus icon
  - Adds new empty fact to the list
  - User can then edit the new fact

**Dependencies:** Task 5.1
**Testing:** Delete and add functionality working in FactExtractionPanel

---

### 6. Testing & Integration

#### 6.1 End-to-End Test: Text Input

- [x] Navigate to `/dashboard/create` page
- [x] Paste text directly into chat component
- [x] AI extracts facts from text
- [x] Facts displayed in FactExtractionPanel
- [x] Edit a fact in the panel
- [x] Click "Continue to Script Generation" (confirms facts)

**Dependencies:** Tasks 3.5, 5.1
**Status:** Working via chat component integration

#### 6.2 End-to-End Test: PDF Upload

- [x] Navigate to `/dashboard/create` page
- [x] Upload PDF via chat component
- [x] PDF text extracted client-side
- [x] AI extracts facts from PDF content
- [x] Facts displayed in FactExtractionPanel
- [x] Remove a fact
- [x] Add a new fact manually
- [x] Confirm facts (ready for next step)

**Dependencies:** Tasks 1.2, 3.5, 5.2
**Status:** Working via chat component integration

#### 6.3 Test Fact Persistence

- [x] Extract facts via chat
- [x] Confirm facts
- [x] Check localStorage: `localStorage.getItem('facts_current')`
- [x] Verify facts are stored as JSON

**Dependencies:** Task 3.3
**Status:** Facts stored in localStorage with key `facts_current`

---

### 7. UI/UX Enhancements

#### 7.1 Chat Display Improvements

- [x] Hide PDF/URL extracted content from chat display:

  - User's original message shown in chat
  - Extracted PDF/URL content sent to AI but not displayed
  - PDF icon indicator shown when materials are processed

- [x] Streaming message handling:

  - Shows "Processing your materials and extracting facts..." during streaming
  - Hides raw JSON code blocks from assistant messages
  - Only shows cleaned conversational text after streaming completes

- [x] JSON code block removal:
  - Removes ```json code blocks from assistant messages
  - Removes standalone JSON objects containing facts
  - Cleans up extra whitespace

**Dependencies:** Task 3.5
**Implementation:** Enhanced `chat-preview.tsx` to filter and format messages appropriately

#### 7.2 Loading States

- [x] Loading spinner in main content area:

  - Shows animated spinner with "Analyzing your materials and extracting facts..." message
  - Appears in `/dashboard/create` page main content area
  - Managed via FactExtractionContext `isExtracting` state

- [x] Loading state management:
  - `setIsExtracting(true)` called when message sent for fact extraction
  - `setIsExtracting(false)` called when facts are extracted or if extraction fails
  - Loading state synchronized between chat and main content

**Dependencies:** Task 3.3
**Implementation:** Loading state shown in main content area, not in chat, for better UX

---

## Phase Checklist

**Before moving to Phase 04, verify:**

- [x] PDF.js library installed and working
- [x] PDF text extraction works
- [x] Fact extraction logic identifies key concepts (via AI agent)
- [x] All 3 input methods work (text, PDF, URL via chat component)
- [x] Text input extracts facts
- [x] PDF upload extracts facts
- [x] Facts are editable
- [x] Facts can be added/removed
- [x] Facts are stored in localStorage
- [x] Facts can be confirmed and ready for next step

---

## Completion Status

**Total Tasks:** 22 (original) + 4 (new sections) = 26 total
**Completed:** 18
**Incomplete/Not Applicable:** 8
**Percentage:** ~69% (18/26)

**Status:** ✅ Mostly Complete - Core functionality implemented with AI agent approach

---

## Notes

### Implementation Approach

- **Fact Extraction:** Uses AI agent (GPT-4o-mini) instead of keyword matching for more accurate and flexible fact extraction
- **Integration:** Fact extraction integrated into existing chat component (`chat-preview.tsx`) rather than separate topic input page
- **State Management:** Uses React Context (`FactExtractionContext`) for managing fact extraction state across components

### Technical Details

- **PDF.js Worker:** Worker file copied to `public/` folder via postinstall script for reliable loading (avoids CDN issues)
- **URL Fetching:** Uses multiple CORS proxy fallbacks (allorigins.win, corsproxy.io, codetabs.com) with 10-second timeout for better reliability
- **Chat Display:** Enhanced to hide extracted content and JSON code blocks, showing only user-friendly messages
- **Loading States:** Loading indicator shown in main content area with spinner, synchronized with extraction process

### Completed Features

- PDF text extraction with type-safe implementation
- URL content fetching with multiple proxy fallbacks
- AI agent-based fact extraction via chat API
- Fact review and editing in FactExtractionPanel
- Add/delete facts functionality
- Facts stored in localStorage
- Clean chat UI with processing indicators
- Loading states in main content area

### Future Enhancements

- Consider adding progress indicator for large PDF processing
- Fact confidence scores can be displayed to users
- Add validation to prevent empty facts from being submitted
- Consider adding fact export/import functionality
