# Phase 04: Narrative Builder (Agent 2) - Next.js Version (Hours 6-12)

**Timeline:** Day 1, Hours 6-12
**Dependencies:** Phase 03 (Fact Extraction)
**Completion:** 0% (0/18 tasks complete)

---

## Overview

Implement Agent 2 (Narrative Builder) which transforms extracted facts into a 4-part educational script using OpenAI GPT-4o-mini. The script generator is integrated into the chat route and triggers automatically after facts are confirmed. Includes frontend script review UI.

---

## Tasks

### 1. Agent 2 Backend Implementation (Hours 6-8)

#### 1.1 Verify OpenAI Dependencies

- [ ] Verify `@ai-sdk/openai` and `ai` packages are installed (already in package.json)
- [ ] Verify `OPENAI_API_KEY` is configured in `frontend/src/env.js` (already exists)

**Dependencies:** Phase 03 complete
**Testing:** OpenAI SDK already available

#### 1.2 Create Agent Base Types

- [ ] Create `frontend/src/types/agent.ts`:

  ```typescript
  export interface AgentInput {
    sessionId: string;
    data: Record<string, unknown>;
    metadata?: Record<string, unknown>;
  }

  export interface AgentOutput {
    success: boolean;
    data: Record<string, unknown>;
    cost: number; // USD
    duration: number; // seconds
    error?: string;
  }
  ```

**Dependencies:** Task 1.1
**Testing:** Import: `import type { AgentInput, AgentOutput } from "@/types/agent"`

#### 1.3 Create Narrative Builder Agent Class

- [ ] Create `frontend/src/server/agents/narrative-builder.ts`:

  ````typescript
  import { openai } from "@ai-sdk/openai";
  import { generateText } from "ai";
  import { env } from "@/env";
  import type { AgentInput, AgentOutput } from "@/types/agent";

  export class NarrativeBuilderAgent {
    async process(input: AgentInput): Promise<AgentOutput> {
      const startTime = Date.now();

      try {
        if (!env.OPENAI_API_KEY) {
          throw new Error("OPENAI_API_KEY is not configured");
        }

        const topic = input.data.topic as string;
        const facts = input.data.facts as Array<{ concept: string; details: string }>;
        const targetDuration = (input.data.target_duration as number) || 60;

        const systemPrompt = this.buildSystemPrompt(targetDuration);
        const userPrompt = this.buildUserPrompt(topic, facts, targetDuration);

        const result = await generateText({
          model: openai("gpt-4o-mini"),
          system: systemPrompt,
          prompt: userPrompt,
          temperature: 0.7,
          maxTokens: 2000,
        });

        const content = result.text;
        if (!content) {
          throw new Error("No content in LLM response");
        }

        // Extract JSON from response (may be wrapped in markdown code blocks)
        const jsonMatch = content.match(/```json\s*([\s\S]*?)\s*```/) || content.match(/\{[\s\S]*\}/);
        const jsonStr = jsonMatch ? (jsonMatch[1] || jsonMatch[0]) : content;
        const scriptData = JSON.parse(jsonStr);

        // Calculate cost (GPT-4o-mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens)
        const inputTokens = result.usage?.promptTokens || 0;
        const outputTokens = result.usage?.completionTokens || 0;
        const cost = (inputTokens * 0.15) / 1_000_000 + (outputTokens * 0.60) / 1_000_000;

        const duration = (Date.now() - startTime) / 1000;

        return {
          success: true,
          data: { script: scriptData },
          cost,
          duration,
        };
      } catch (error) {
        return {
          success: false,
          data: {},
          cost: 0.0,
          duration: (Date.now() - startTime) / 1000,
          error: error instanceof Error ? error.message : String(error),
        };
      }
    }

    private buildSystemPrompt(targetDuration: number): string {
      return `You are an expert middle school science educator specializing in creating engaging, accurate educational video scripts.
  ````

Your task:

1. Create a 4-part educational script (Hook → Concept → Process → Conclusion)
2. Each part has specific timing and purpose
3. Use age-appropriate language for grades 6-7 (reading level ~6.5)
4. Include all provided facts and key concepts
5. Provide visual guidance for each segment
6. Ensure scientific accuracy

Structure:

- Hook (0-10s): Engage with question or surprising fact
- Concept Introduction (10-25s): Introduce key vocabulary and ideas
- Process Explanation (25-45s): Explain how/why it works with details
- Conclusion (45-60s): Real-world connection and summary

Rules:

- Total duration must be ${targetDuration} seconds
- Use conversational, enthusiastic tone
- Define technical terms when first introduced
- Include concrete examples
- End with memorable takeaway
- Output ONLY valid JSON, no additional text

Required JSON structure:
{
"total_duration": ${targetDuration},
"reading_level": "6.5",
"key_terms_count": <number>,
"segments": [
{
"id": "seg_001",
"type": "hook",
"start_time": 0,
"duration": 10,
"narration": "<script text>",
"visual_guidance": "<description of what should be shown>",
"key_concepts": ["<concept1>", "<concept2>"],
"educational_purpose": "<why this segment matters>"
},
{
"id": "seg_002",
"type": "concept_introduction",
"start_time": 10,
"duration": 15,
"narration": "<script text>",
"visual_guidance": "<description>",
"key_concepts": [],
"educational_purpose": "<purpose>"
},
{
"id": "seg_003",
"type": "process_explanation",
"start_time": 25,
"duration": 20,
"narration": "<script text>",
"visual_guidance": "<description>",
"key_concepts": [],
"educational_purpose": "<purpose>"
},
{
"id": "seg_004",
"type": "conclusion",
"start_time": 45,
"duration": 15,
"narration": "<script text>",
"visual_guidance": "<description>",
"key_concepts": [],
"educational_purpose": "<purpose>"
}
]
}`;
}

    private buildUserPrompt(
      topic: string,
      facts: Array<{ concept: string; details: string }>,
      targetDuration: number
    ): string {
      const factsStr = facts.map((f) => `- ${f.concept}: ${f.details}`).join("\n");

      return `Topic: ${topic}

Key Facts to Include:
${factsStr}

Target Duration: ${targetDuration} seconds
Grade Level: 6-7

Generate an engaging, scientifically accurate educational script in JSON format.`;
}
}

````

**Dependencies:** Task 1.2
**Testing:** Instantiate: `const agent = new NarrativeBuilderAgent()`

#### 1.4 Test Narrative Builder Agent
- [ ] Create `frontend/src/server/agents/__tests__/narrative-builder.test.ts`:
```typescript
import { NarrativeBuilderAgent } from "../narrative-builder";
import type { AgentInput } from "@/types/agent";

async function testAgent() {
  const agent = new NarrativeBuilderAgent();

  const input: AgentInput = {
    sessionId: "test-1",
    data: {
      topic: "Photosynthesis",
      facts: [
        { concept: "photosynthesis", details: "Process where plants make food from sunlight" },
        { concept: "chlorophyll", details: "Green pigment that captures light" },
        { concept: "glucose", details: "Sugar produced as plant food" },
      ],
      target_duration: 60,
    },
  };

  const result = await agent.process(input);
  console.log("Success:", result.success);
  console.log("Cost:", `$${result.cost.toFixed(4)}`);
  console.log("Duration:", `${result.duration.toFixed(2)}s`);
  if (result.success) {
    const script = result.data.script as { segments: unknown[] };
    console.log("Script segments:", script.segments.length);
  } else {
    console.log("Error:", result.error);
  }
}

testAgent().catch(console.error);
````

- [ ] Run: `bun run src/server/agents/__tests__/narrative-builder.test.ts`
- [ ] Verify 4 segments returned

**Dependencies:** Task 1.3
**Testing:** Should return script with 4 segments, cost ~$0.01-0.02

---

### 2. Script Generation Integration (Hours 8-10)

#### 2.1 Create Database Schema for Sessions and Assets

- [ ] Create `frontend/src/server/db/schema/sessions.ts`:

  ```typescript
  import {
    pgTable,
    text,
    timestamp,
    jsonb,
    varchar,
  } from "drizzle-orm/pg-core";
  import { users } from "../auth/schema";

  export const sessions = pgTable("sessions", {
    id: text("id").primaryKey(),
    userId: text("user_id")
      .notNull()
      .references(() => users.id),
    status: varchar("status", { length: 50 }).notNull().default("created"),
    topic: varchar("topic", { length: 200 }),
    learningObjective: text("learning_objective"),
    confirmedFacts: jsonb("confirmed_facts"),
    generatedScript: jsonb("generated_script"),
    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at").defaultNow().notNull(),
  });

  export const assets = pgTable("assets", {
    id: text("id").primaryKey(),
    sessionId: text("session_id")
      .notNull()
      .references(() => sessions.id),
    assetType: varchar("asset_type", { length: 50 }).notNull(),
    url: text("url"),
    metadata: jsonb("metadata"),
    createdAt: timestamp("created_at").defaultNow().notNull(),
  });
  ```

- [ ] Update `frontend/src/server/db/schema.ts` to export sessions and assets
- [ ] Run migration: `bun run db:generate && bun run db:push`

**Dependencies:** Phase 01
**Testing:** Tables created in database

#### 2.2 Create Script Generation Helper Function

- [ ] Create `frontend/src/server/utils/generate-script.ts`:

  ```typescript
  import { NarrativeBuilderAgent } from "@/server/agents/narrative-builder";
  import { db } from "@/server/db";
  import { sessions, assets } from "@/server/db/schema/sessions";
  import { eq } from "drizzle-orm";
  import { nanoid } from "nanoid";

  export async function generateScriptForSession(
    sessionId: string,
    userId: string,
    topic: string,
    facts: Array<{ concept: string; details: string }>,
    targetDuration: number = 60
  ) {
    // Verify session ownership
    const session = await db.query.sessions.findFirst({
      where: eq(sessions.id, sessionId),
    });

    if (!session || session.userId !== userId) {
      throw new Error("Session not found or unauthorized");
    }

    const agent = new NarrativeBuilderAgent();
    const result = await agent.process({
      sessionId,
      data: {
        topic,
        facts,
        target_duration: targetDuration,
      },
    });

    if (!result.success) {
      throw new Error(result.error || "Script generation failed");
    }

    // Save script to database as asset
    const assetId = nanoid();
    await db.insert(assets).values({
      id: assetId,
      sessionId,
      assetType: "script",
      url: "",
      metadata: {
        script: result.data.script,
        cost: result.cost,
        duration: result.duration,
      },
    });

    // Update session status
    await db
      .update(sessions)
      .set({
        status: "script_generated",
        generatedScript: result.data.script,
        updatedAt: new Date(),
      })
      .where(eq(sessions.id, sessionId));

    return result.data.script;
  }
  ```

**Dependencies:** Tasks 1.3, 2.1
**Testing:** Function generates and saves script

#### 2.3 Integrate Script Generation into Chat Route

- [ ] Update `frontend/src/app/api/chat/route.ts` to detect fact confirmation and trigger script generation:
  - Add import: `import { generateScriptForSession } from "@/server/utils/generate-script";`
  - Add import: `import { db } from "@/server/db";`
  - Add import: `import { sessions } from "@/server/db/schema/sessions";`
  - Add import: `import { parseFactsFromMessage } from "@/lib/factParsing";`
  - After streaming response, check if user confirmed facts (look for patterns like "yes", "approve", "confirm", "continue")
  - If confirmed, extract facts and topic from assistant messages
  - Get or create a session for the user (store sessionId for frontend to use)
  - Call `generateScriptForSession` in background (fire and forget)
  - Return sessionId in response or store it somewhere accessible to frontend
  - Note: This should happen after the streaming response is sent

**Dependencies:** Task 2.2
**Testing:** Script generation triggers after fact confirmation in chat, sessionId is available

#### 2.4 Test Script Generation Integration

- [ ] Test chat flow: extract facts → confirm → verify script generation triggers
- [ ] Verify script is saved to database
- [ ] Check session status is updated

**Dependencies:** Tasks 2.2, 2.3
**Testing:** End-to-end flow works

---

### 3. Script Review Frontend (Hours 10-12)

#### 3.1 Create tRPC Router to Fetch Script

- [ ] Create `frontend/src/server/api/routers/script.ts`:

  ```typescript
  import { z } from "zod";
  import { TRPCError } from "@trpc/server";
  import { createTRPCRouter, protectedProcedure } from "@/server/api/trpc";
  import { db } from "@/server/db";
  import { sessions, assets } from "@/server/db/schema/sessions";
  import { eq } from "drizzle-orm";

  export const scriptRouter = createTRPCRouter({
    get: protectedProcedure
      .input(z.object({ sessionId: z.string() }))
      .query(async ({ input, ctx }) => {
        if (!ctx.session?.user?.id) {
          throw new TRPCError({
            code: "UNAUTHORIZED",
            message: "User not authenticated",
          });
        }

        const session = await db.query.sessions.findFirst({
          where: eq(sessions.id, input.sessionId),
        });

        if (!session || session.userId !== ctx.session.user.id) {
          throw new TRPCError({
            code: "NOT_FOUND",
            message: "Session not found",
          });
        }

        // Get script asset
        const scriptAsset = await db.query.assets.findFirst({
          where: eq(assets.sessionId, input.sessionId),
        });

        if (!scriptAsset || scriptAsset.assetType !== "script") {
          return null;
        }

        return {
          script: scriptAsset.metadata?.script,
          cost: scriptAsset.metadata?.cost,
          duration: scriptAsset.metadata?.duration,
        };
      }),
  });
  ```

- [ ] Register router in `frontend/src/server/api/root.ts`:

  ```typescript
  import { scriptRouter } from "./routers/script";

  export const appRouter = createTRPCRouter({
    storage: storageRouter,
    script: scriptRouter,
  });
  ```

**Dependencies:** Task 2.1
**Testing:** Router registered successfully

#### 3.2 Create Script Display Component

- [ ] Create `frontend/src/components/generation/ScriptReviewPanel.tsx`:

  ```typescript
  "use client";

  import { useState, useEffect } from "react";
  import { api } from "@/trpc/react";
  import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
  } from "@/components/ui/card";
  import { Button } from "@/components/ui/button";

  interface Segment {
    id: string;
    type: string;
    start_time: number;
    duration: number;
    narration: string;
    visual_guidance: string;
    key_concepts: string[];
    educational_purpose: string;
  }

  interface ScriptReviewPanelProps {
    sessionId: string | null;
  }

  export function ScriptReviewPanel({ sessionId }: ScriptReviewPanelProps) {
    const {
      data: scriptData,
      isLoading,
      refetch,
    } = api.script.get.useQuery(
      { sessionId: sessionId ?? "" },
      { enabled: !!sessionId }
    );
    const [editableSegments, setEditableSegments] = useState<Segment[]>([]);

    // Poll for script if sessionId exists but script not found yet
    useEffect(() => {
      if (sessionId && !scriptData?.script && !isLoading) {
        const interval = setInterval(() => {
          refetch();
        }, 2000); // Poll every 2 seconds
        return () => clearInterval(interval);
      }
    }, [sessionId, scriptData, isLoading, refetch]);

    // Update editable segments when script data loads
    useEffect(() => {
      if (scriptData?.script && "segments" in scriptData.script) {
        setEditableSegments(
          (scriptData.script as { segments: Segment[] }).segments
        );
      }
    }, [scriptData]);

    const handleApprove = () => {
      // Store approved script in session
      // TODO: Save approved script to database
      // TODO: Navigate to next phase (visual generation)
      alert("Script approved! Visual generation coming in next phase.");
    };

    const handleRegenerateSegment = (index: number) => {
      alert("Regeneration feature coming in Phase 04.2");
    };

    if (!sessionId) {
      return null;
    }

    if (isLoading || !scriptData?.script) {
      return (
        <Card>
          <CardHeader>
            <CardTitle>Generating Script...</CardTitle>
            <CardDescription>
              AI is creating your educational script from the confirmed facts.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <div className="border-primary size-5 animate-spin rounded-full border-2 border-t-transparent" />
              <p className="text-muted-foreground">
                This usually takes 3-5 seconds...
              </p>
            </div>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card>
        <CardHeader>
          <CardTitle>Review Script</CardTitle>
          <CardDescription>
            Review and edit the generated script. Each segment can be modified
            before approval.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {editableSegments.map((segment, index) => (
              <div
                key={segment.id}
                className="border-l-primary bg-muted/50 rounded-lg border-l-4 p-4"
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <span className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded text-sm font-medium">
                      Segment {index + 1}: {segment.type}
                    </span>
                    <span className="ml-3 text-sm text-muted-foreground">
                      {segment.start_time}s -{" "}
                      {segment.start_time + segment.duration}s
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRegenerateSegment(index)}
                  >
                    Regenerate
                  </Button>
                </div>

                <div className="mb-3">
                  <label className="block text-sm font-medium mb-2">
                    Narration:
                  </label>
                  <textarea
                    value={segment.narration}
                    onChange={(e) => {
                      const updated = [...editableSegments];
                      updated[index].narration = e.target.value;
                      setEditableSegments(updated);
                    }}
                    className="w-full border rounded px-3 py-2 min-h-[80px] text-sm"
                  />
                </div>

                <div className="mb-3">
                  <label className="block text-sm font-medium mb-2">
                    Visual Guidance:
                  </label>
                  <textarea
                    value={segment.visual_guidance}
                    onChange={(e) => {
                      const updated = [...editableSegments];
                      updated[index].visual_guidance = e.target.value;
                      setEditableSegments(updated);
                    }}
                    className="w-full border rounded px-3 py-2 text-sm"
                    rows={2}
                  />
                </div>

                {segment.key_concepts.length > 0 && (
                  <div className="text-sm">
                    <span className="font-medium">Key Concepts:</span>{" "}
                    {segment.key_concepts.join(", ")}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="mt-6 flex gap-4">
            <Button onClick={handleApprove} size="lg">
              Approve Script & Generate Visuals →
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }
  ```

**Dependencies:** Task 3.1
**Testing:** Component displays script when available

#### 3.3 Update Create Page to Display Script

- [ ] Update `frontend/src/app/dashboard/create/page.tsx`:
  - Import `ScriptReviewPanel` component
  - Add state or context to track current session ID
  - Display `ScriptReviewPanel` in main content area when script is available
  - Show script panel after facts are confirmed and script is generated
  - Update step indicator to show "Step 3: Review Script" when script is available

**Dependencies:** Task 3.2
**Testing:** Script displays in main area after generation

#### 3.4 Update Fact Extraction to Track Session

- [ ] Update `frontend/src/components/fact-extraction/FactExtractionContext.tsx` or create session management:
  - Add sessionId state to track current video generation session
  - Create or retrieve session when facts are confirmed
  - Pass sessionId to ScriptReviewPanel component

**Dependencies:** Task 2.3
**Testing:** Session ID is available for script fetching

#### 3.5 Test Script Review Flow

- [ ] Complete fact extraction
- [ ] Confirm facts in chat
- [ ] Verify script generation triggers automatically
- [ ] Verify script displays in main area (not separate page)
- [ ] Verify script displays with 4 segments
- [ ] Edit a segment's narration
- [ ] Click "Approve Script"
- [ ] Verify script saved to database
- [ ] Verify user stays on /dashboard/create page throughout

**Dependencies:** Tasks 3.2, 3.3, 3.4
**Testing:** End-to-end flow should work on single page

---

## Phase Checklist

**Before moving to Phase 05, verify:**

- [ ] OpenAI API key configured
- [ ] Narrative Builder Agent generates 4-segment script
- [ ] Script generation triggers automatically after fact confirmation in chat
- [ ] Script saved to database as Asset
- [ ] Frontend displays loading state in main area
- [ ] Frontend receives and displays script via tRPC in main content area
- [ ] Script segments are editable on the same page
- [ ] Approved script saved to database
- [ ] User stays on /dashboard/create page throughout the flow

---

## Completion Status

**Total Tasks:** 19
**Completed:** 0
**Percentage:** 0%

**Status:** ⏳ Not Started

---

## Notes

- OpenAI GPT-4o-mini costs ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- Expected cost per script: $0.01-0.02
- Script generation typically takes 3-5 seconds
- Consider adding retry logic if LLM fails
- Add validation to ensure script has exactly 4 segments
- Consider caching common scripts to reduce costs
- Script generation is integrated into chat route flow (no separate WebSocket/SSE needed)
- Database schema needs to be created for sessions and assets tables
- Script review happens in the main content area of /dashboard/create page (no separate page)
- User stays on the same page throughout: chat on left, main content on right
