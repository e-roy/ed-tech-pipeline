import { openai } from "@ai-sdk/openai";
import { generateObject } from "ai";
import { z } from "zod";
import { env } from "@/env";
import { S3Client, CopyObjectCommand } from "@aws-sdk/client-s3";
import { listSessionFiles } from "./storage";
import type { Narration } from "@/types";
import { db } from "@/server/db";
import { videoSessions } from "@/server/db/schema";
import { eq } from "drizzle-orm";

const imageAnalysisSchema = z.object({
  relevanceScore: z.number().min(0).max(10),
  reasoning: z.string(),
  hasRelevantDiagrams: z.boolean(),
  matchedConcepts: z.array(z.string()),
});

function getS3Client(): S3Client {
  const s3Client = new S3Client({
    region: env.AWS_REGION,
    credentials: {
      accessKeyId: env.AWS_ACCESS_KEY_ID ?? "",
      secretAccessKey: env.AWS_SECRET_ACCESS_KEY ?? "",
    },
  });

  return s3Client;
}

/**
 * Analyze a single image against the narration using OpenAI vision model
 */
async function analyzeImageRelevance(
  imageUrl: string,
  narration: Narration,
  facts: Array<{ concept: string; details: string }>,
  imageIndex: number,
): Promise<{
  score: number;
  reasoning: string;
  hasRelevantDiagrams: boolean;
  matchedConcepts: string[];
}> {
  // Extract just the narration text from the 4 segments
  const narrationText = narration.segments.map((s) => s.narration).join("\n\n");

  const systemPrompt = `You are an expert at analyzing educational diagrams and images for their relevance to lesson content.

Your task is to identify ONLY substantive educational diagrams, charts, or illustrations that would help students learn the concepts.

**REJECT these types of images (score 0-2, hasRelevantDiagrams: false):**
- Footers with contact information, URLs, or references
- Headers with logos or titles only
- Simple text-only images without diagrams
- Copyright notices or attribution sections
- Decorative borders or page numbers
- Single photographs without labels or annotations
- Images that are just color blocks or simple shapes

**ACCEPT these types of images (score 6-10, hasRelevantDiagrams: true):**
- Process diagrams showing steps or cycles (e.g., photosynthesis cycle, water cycle)
- Labeled scientific diagrams (e.g., cell structures, anatomical drawings)
- Charts and graphs showing data or relationships
- Concept maps or flow charts
- Annotated illustrations that explain mechanisms
- Before/after comparisons with labels
- Cross-sections or cutaway views showing internal structures

**Scoring criteria:**
- 9-10: Perfect educational diagram directly illustrating key concepts with clear labels
- 7-8: Strong diagram showing relevant concepts with good visual clarity
- 6: Acceptable diagram that somewhat relates to the topic
- 4-5: Marginally relevant or unclear diagram
- 0-3: Not educational content (footer, header, decorative, or off-topic)

**Key questions to ask:**
1. Does this image TEACH or EXPLAIN a concept visually?
2. Does it contain labels, arrows, or annotations that aid understanding?
3. Would a student learn something concrete from looking at this?
4. Is it a substantive diagram (not just a logo, footer, or text block)?

Be STRICT: When in doubt, give a lower score. Only images that clearly illustrate educational concepts should get hasRelevantDiagrams: true.

Provide:
- relevanceScore: 0-10 (be strict, most images should be 0-5)
- reasoning: Brief explanation focusing on what makes it educational or not
- hasRelevantDiagrams: true ONLY if it's a substantive educational diagram
- matchedConcepts: Array of concepts this image actually illustrates`;

  const userPrompt = `Selected Facts (Teacher-chosen concepts):
${facts.map((f) => `- ${f.concept}: ${f.details}`).join("\n")}

Narration Script:
${narrationText}

Analyze how well this image supports these educational concepts and narration.`;

  try {
    const result = await generateObject({
      model: openai("gpt-4o-mini"),
      messages: [
        {
          role: "system",
          content: systemPrompt,
        },
        {
          role: "user",
          content: [
            {
              type: "text",
              text: userPrompt,
            },
            {
              type: "image",
              image: new URL(imageUrl),
            },
          ],
        },
      ],
      schema: imageAnalysisSchema,
    });

    return {
      score: result.object.relevanceScore,
      reasoning: result.object.reasoning,
      hasRelevantDiagrams: result.object.hasRelevantDiagrams,
      matchedConcepts: result.object.matchedConcepts,
    };
  } catch (error) {
    console.error(`Failed to analyze image ${imageIndex}:`, error);
    return {
      score: 0,
      reasoning: "Analysis failed",
      hasRelevantDiagrams: false,
      matchedConcepts: [],
    };
  }
}

/**
 * Copy an S3 object from one key to another
 */
async function copyS3Object(
  sourceKey: string,
  destinationKey: string,
): Promise<void> {
  if (!env.S3_BUCKET_NAME) {
    throw new Error("S3_BUCKET_NAME not configured");
  }

  const client = getS3Client();

  await client.send(
    new CopyObjectCommand({
      Bucket: env.S3_BUCKET_NAME,
      CopySource: `${env.S3_BUCKET_NAME}/${sourceKey}`,
      Key: destinationKey,
    }),
  );
}

/**
 * Select and copy the best 1-2 diagrams from PDF images to diagrams folder
 */
export async function selectAndCopyDiagrams(
  userId: string,
  sessionId: string,
  narration: Narration,
  facts?: Array<{ concept: string; details: string }>,
): Promise<{
  success: boolean;
  selectedCount: number;
  totalAnalyzed: number;
  cost: number;
  error?: string;
}> {
  try {
    if (!env.OPENAI_API_KEY) {
      throw new Error("OPENAI_API_KEY not configured");
    }

    console.log(`[selectAndCopyDiagrams] Starting for session ${sessionId}`);

    // 1. Load confirmed facts from database if not provided
    let factsToUse: Array<{ concept: string; details: string }> = facts ?? [];

    if (factsToUse.length === 0) {
      const [session] = await db
        .select({
          confirmedFacts: videoSessions.confirmedFacts,
        })
        .from(videoSessions)
        .where(eq(videoSessions.id, sessionId))
        .limit(1);

      if (session?.confirmedFacts && Array.isArray(session.confirmedFacts)) {
        factsToUse = session.confirmedFacts as Array<{
          concept: string;
          details: string;
        }>;
      }
    }

    console.log(
      `[selectAndCopyDiagrams] Using ${factsToUse.length} facts for analysis`,
    );

    // 2. List all images from pdf-images folder
    const images = await listSessionFiles(userId, sessionId, "pdf-images");

    if (images.length === 0) {
      console.log(
        `[selectAndCopyDiagrams] No images found in pdf-images folder`,
      );
      return {
        success: true,
        selectedCount: 0,
        totalAnalyzed: 0,
        cost: 0,
      };
    }

    console.log(
      `[selectAndCopyDiagrams] Found ${images.length} images to analyze`,
    );

    // 3. Analyze each image with vision model
    const analyses = await Promise.all(
      images.map((img, idx) =>
        analyzeImageRelevance(img.presigned_url, narration, factsToUse, idx),
      ),
    );

    // 4. Select top 1-2 images based on score
    const rankedImages = images
      .map((img, idx) => ({
        ...img,
        analysis: analyses[idx]!,
      }))
      .filter(
        (img) => img.analysis.hasRelevantDiagrams && img.analysis.score >= 6,
      )
      .sort((a, b) => b.analysis.score - a.analysis.score)
      .slice(0, 2);

    console.log(
      `[selectAndCopyDiagrams] Selected ${rankedImages.length} images:`,
      rankedImages.map((img) => ({
        name: img.name,
        score: img.analysis.score,
        reasoning: img.analysis.reasoning,
      })),
    );

    // 5. Copy selected images to diagrams folder
    for (const [idx, image] of rankedImages.entries()) {
      const sourceKey = image.key;
      const fileName = `diagram_${idx + 1}_${image.name}`;
      const destinationKey = `users/${userId}/${sessionId}/diagrams/${fileName}`;

      await copyS3Object(sourceKey, destinationKey);
      console.log(
        `[selectAndCopyDiagrams] Copied ${sourceKey} to ${destinationKey}`,
      );
    }

    // Calculate approximate cost
    // gpt-4o-mini vision: ~$0.00015 per image
    const cost = images.length * 0.00015;

    return {
      success: true,
      selectedCount: rankedImages.length,
      totalAnalyzed: images.length,
      cost,
    };
  } catch (error) {
    console.error("[selectAndCopyDiagrams] Error:", error);
    return {
      success: false,
      selectedCount: 0,
      totalAnalyzed: 0,
      cost: 0,
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}
