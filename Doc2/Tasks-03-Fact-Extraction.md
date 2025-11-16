# Phase 03: Fact Extraction (Next.js) (Hours 4-6)

**Timeline:** Day 1, Hours 4-6
**Dependencies:** Phase 02 (Auth & Session Management)
**Completion:** 0% (0/22 tasks complete)

---

## Overview

Implement client-side fact extraction from PDF files, URLs, and text input. This Next.js-based extraction reduces backend costs by processing documents in the browser.

---

## Tasks

### 1. PDF Extraction Setup

#### 1.1 Install PDF.js Library
- [ ] Install pdf.js: `npm install pdfjs-dist`
- [ ] Create `frontend/lib/pdfWorker.ts`:
  ```typescript
  import * as pdfjsLib from 'pdfjs-dist';

  // Set worker path
  pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

  export default pdfjsLib;
  ```

**Dependencies:** Phase 02 complete
**Testing:** Import: `import pdfjsLib from '@/lib/pdfWorker'`

#### 1.2 Create PDF Text Extraction Function
- [ ] Create `frontend/lib/extractPDF.ts`:
  ```typescript
  import pdfjsLib from './pdfWorker';

  export async function extractTextFromPDF(file: File): Promise<string> {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

    let fullText = '';

    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
      const page = await pdf.getPage(pageNum);
      const textContent = await page.getTextContent();
      const pageText = textContent.items
        .map((item: any) => item.str)
        .join(' ');
      fullText += pageText + '\n';
    }

    return fullText;
  }
  ```

**Dependencies:** Task 1.1
**Testing:** Test with sample PDF file

#### 1.3 Test PDF Extraction
- [ ] Create test component `frontend/components/TestPDFExtraction.tsx`:
  ```typescript
  'use client';
  import { useState } from 'react';
  import { extractTextFromPDF } from '@/lib/extractPDF';

  export default function TestPDFExtraction() {
    const [text, setText] = useState('');

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        const extracted = await extractTextFromPDF(file);
        setText(extracted);
      }
    };

    return (
      <div className="p-4">
        <input type="file" accept=".pdf" onChange={handleFileUpload} />
        <pre className="mt-4 whitespace-pre-wrap">{text}</pre>
      </div>
    );
  }
  ```
- [ ] Upload a test PDF
- [ ] Verify text extraction works

**Dependencies:** Task 1.2
**Testing:** Should display extracted text from PDF

---

### 2. Fact Extraction Logic

#### 2.1 Create Concept Detection Function
- [ ] Create `frontend/lib/extractFacts.ts`:
  ```typescript
  export interface Fact {
    concept: string;
    details: string;
    confidence: number;
  }

  export function extractFacts(text: string): Fact[] {
    const facts: Fact[] = [];

    // Simple keyword-based extraction (can be enhanced with NLP)
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);

    // Keywords that indicate important concepts
    const keywordPatterns = [
      /photosynthesis/i,
      /chlorophyll/i,
      /carbon dioxide|CO2/i,
      /oxygen|O2/i,
      /glucose/i,
      /solar system/i,
      /planet/i,
      /gravity/i,
      /cell/i,
      /nucleus/i,
      /mitochondria/i,
      /DNA/i,
      /water cycle/i,
      /evaporation/i,
      /condensation/i,
      /precipitation/i,
    ];

    sentences.forEach(sentence => {
      keywordPatterns.forEach(pattern => {
        if (pattern.test(sentence)) {
          const concept = sentence.match(pattern)?.[0] || '';
          facts.push({
            concept: concept,
            details: sentence.trim(),
            confidence: 0.8
          });
        }
      });
    });

    // Deduplicate
    const uniqueFacts = facts.filter((fact, index, self) =>
      index === self.findIndex(f => f.concept.toLowerCase() === fact.concept.toLowerCase())
    );

    return uniqueFacts.slice(0, 10); // Limit to 10 facts
  }
  ```

**Dependencies:** None (pure function)
**Testing:** Test with sample text: `extractFacts("Photosynthesis is the process...")`

#### 2.2 Test Fact Extraction
- [ ] Create test function:
  ```typescript
  const sampleText = `
    Photosynthesis is the process by which plants use sunlight to convert
    carbon dioxide and water into glucose and oxygen. Chlorophyll is the
    green pigment in plants that captures light energy.
  `;
  const facts = extractFacts(sampleText);
  console.log(facts);
  ```
- [ ] Should extract concepts: photosynthesis, chlorophyll, carbon dioxide, oxygen, glucose

**Dependencies:** Task 2.1
**Testing:** Verify at least 3-5 facts extracted

---

### 3. Topic Input Page

#### 3.1 Create Topic Input Component
- [ ] Create `frontend/app/session/[id]/topic-input/page.tsx`:
  ```typescript
  'use client';
  import { useState } from 'react';
  import { useParams, useRouter } from 'next/navigation';
  import { extractTextFromPDF } from '@/lib/extractPDF';
  import { extractFacts, Fact } from '@/lib/extractFacts';

  export default function TopicInputPage() {
    const params = useParams();
    const router = useRouter();
    const sessionId = params.id;

    const [inputMethod, setInputMethod] = useState<'text' | 'pdf' | 'url'>('text');
    const [textInput, setTextInput] = useState('');
    const [urlInput, setUrlInput] = useState('');
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
        console.error('PDF extraction error:', error);
        alert('Failed to extract text from PDF');
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
      localStorage.setItem(`facts_${sessionId}`, JSON.stringify(extractedFacts));
      router.push(`/session/${sessionId}/script-review`);
    };

    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <h1 className="text-3xl font-bold mb-6">Input Learning Material</h1>
        <p className="text-gray-600 mb-6">Session ID: {sessionId}</p>

        {/* Input method selector */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setInputMethod('text')}
            className={`px-4 py-2 rounded ${inputMethod === 'text' ? 'bg-blue-600 text-white' : 'bg-white'}`}
          >
            Text Input
          </button>
          <button
            onClick={() => setInputMethod('pdf')}
            className={`px-4 py-2 rounded ${inputMethod === 'pdf' ? 'bg-blue-600 text-white' : 'bg-white'}`}
          >
            Upload PDF
          </button>
          <button
            onClick={() => setInputMethod('url')}
            className={`px-4 py-2 rounded ${inputMethod === 'url' ? 'bg-blue-600 text-white' : 'bg-white'}`}
          >
            URL
          </button>
        </div>

        {/* Input forms */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          {inputMethod === 'text' && (
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

          {inputMethod === 'pdf' && (
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

          {inputMethod === 'url' && (
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
            <h2 className="text-xl font-bold mb-4">Extracted Facts ({extractedFacts.length})</h2>
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
- [ ] Create `frontend/lib/fetchURL.ts`:
  ```typescript
  export async function fetchURLContent(url: string): Promise<string> {
    try {
      // Use a CORS proxy for client-side fetching
      const proxyUrl = 'https://api.allorigins.win/get?url=';
      const response = await fetch(proxyUrl + encodeURIComponent(url));
      const data = await response.json();

      // Strip HTML tags (basic)
      const text = data.contents.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ');
      return text;
    } catch (error) {
      console.error('URL fetch error:', error);
      throw new Error('Failed to fetch URL content');
    }
  }
  ```

**Dependencies:** None
**Testing:** Test with public URL

#### 4.2 Add URL Fetching to Topic Input
- [ ] Update Topic Input page to handle URL submission:
  ```typescript
  const handleURLSubmit = async () => {
    setLoading(true);
    try {
      const text = await fetchURLContent(urlInput);
      const facts = extractFacts(text);
      setExtractedFacts(facts);
    } catch (error) {
      alert('Failed to fetch URL content');
    } finally {
      setLoading(false);
    }
  };
  ```
- [ ] Add submit button for URL input method

**Dependencies:** Tasks 3.1, 4.1
**Testing:** Enter URL, extract facts from webpage

---

### 5. Fact Review & Editing

#### 5.1 Make Facts Editable
- [ ] Update fact display to allow editing:
  ```typescript
  {extractedFacts.map((fact, index) => (
    <div key={index} className="border-l-4 border-blue-500 pl-4">
      <input
        type="text"
        value={fact.concept}
        onChange={(e) => {
          const updated = [...extractedFacts];
          updated[index].concept = e.target.value;
          setExtractedFacts(updated);
        }}
        className="font-semibold border-b border-transparent hover:border-gray-300 focus:border-blue-500"
      />
      <textarea
        value={fact.details}
        onChange={(e) => {
          const updated = [...extractedFacts];
          updated[index].details = e.target.value;
          setExtractedFacts(updated);
        }}
        className="w-full text-sm text-gray-600 border-b border-transparent hover:border-gray-300 focus:border-blue-500"
        rows={2}
      />
    </div>
  ))}
  ```

**Dependencies:** Task 3.1
**Testing:** Click on fact, edit text, verify updates

#### 5.2 Add Fact Management Actions
- [ ] Add delete button for each fact:
  ```typescript
  <button
    onClick={() => {
      setExtractedFacts(extractedFacts.filter((_, i) => i !== index));
    }}
    className="text-red-600 text-sm hover:underline"
  >
    Remove
  </button>
  ```
- [ ] Add "Add Fact" button:
  ```typescript
  <button
    onClick={() => {
      setExtractedFacts([...extractedFacts, { concept: '', details: '', confidence: 1.0 }]);
    }}
    className="bg-gray-200 px-4 py-2 rounded hover:bg-gray-300"
  >
    + Add Fact
  </button>
  ```

**Dependencies:** Task 5.1
**Testing:** Delete fact, add new fact manually

---

### 6. Testing & Integration

#### 6.1 End-to-End Test: Text Input
- [ ] Navigate to topic input page
- [ ] Select "Text Input"
- [ ] Paste sample text about photosynthesis
- [ ] Click "Extract Facts"
- [ ] Verify facts are extracted and displayed
- [ ] Edit a fact
- [ ] Click "Continue to Script Generation"

**Dependencies:** Tasks 3.1, 5.1
**Testing:** Should successfully extract and display facts

#### 6.2 End-to-End Test: PDF Upload
- [ ] Navigate to topic input page
- [ ] Select "Upload PDF"
- [ ] Upload a sample educational PDF
- [ ] Verify text extraction and fact display
- [ ] Remove a fact
- [ ] Add a new fact manually
- [ ] Continue to next step

**Dependencies:** Tasks 1.2, 3.1, 5.2
**Testing:** Should handle PDF upload and extraction

#### 6.3 Test Fact Persistence
- [ ] Extract facts
- [ ] Continue to next page
- [ ] Check localStorage: `localStorage.getItem('facts_1')`
- [ ] Verify facts are stored as JSON

**Dependencies:** Task 3.1
**Testing:** Should see facts JSON in localStorage

---

## Phase Checklist

**Before moving to Phase 04, verify:**

- [ ] PDF.js library installed and working
- [ ] PDF text extraction works
- [ ] Fact extraction logic identifies key concepts
- [ ] Topic input page renders all 3 input methods
- [ ] Text input extracts facts
- [ ] PDF upload extracts facts
- [ ] Facts are editable
- [ ] Facts can be added/removed
- [ ] Facts are stored in localStorage
- [ ] Navigation to next page works

---

## Completion Status

**Total Tasks:** 22
**Completed:** 0
**Percentage:** 0%

**Status:** ⏳ Not Started

---

## Notes

- Fact extraction is basic keyword matching - can be enhanced with NLP libraries
- URL fetching uses CORS proxy - may have rate limits
- Consider adding progress indicator for PDF processing
- Fact confidence scores can be displayed to users
- Add validation to prevent empty facts from being submitted
