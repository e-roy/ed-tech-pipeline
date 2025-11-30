import { auth } from "@/server/auth";
import { db } from "@/server/db";
import { videoSessions } from "@/server/db/schema";
import { eq } from "drizzle-orm";
import { uploadImageToS3 } from "@/server/services/pdf-storage";

export const runtime = "nodejs";
export const maxDuration = 60; // Image processing can take time

export async function POST(req: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return new Response("Unauthorized", { status: 401 });
    }

    const formData = await req.formData();
    const sessionId = formData.get("sessionId") as string;
    const imageCount = parseInt(formData.get("imageCount") as string) || 0;

    if (!sessionId) {
      return new Response("Missing sessionId", { status: 400 });
    }

    // Verify session belongs to user
    const [sessionData] = await db
      .select({ sourceMaterials: videoSessions.sourceMaterials })
      .from(videoSessions)
      .where(eq(videoSessions.id, sessionId))
      .limit(1);

    if (!sessionData) {
      return new Response("Session not found", { status: 404 });
    }

    // Upload images to S3
    const imageUrls: string[] = [];
    for (let i = 0; i < imageCount; i++) {
      const imageBlob = formData.get(`image_${i}`) as File;
      if (imageBlob) {
        const imageBuffer = Buffer.from(await imageBlob.arrayBuffer());

        // Extract page number from filename (e.g., "page_1_img_0.png")
        const regex = /page_(\d+)_img_(\d+)/;
        const match = regex.exec(imageBlob.name);
        const pageNumber = match?.[1] ? parseInt(match[1]) : i + 1;
        const imageIndex = match?.[2] ? parseInt(match[2]) : 0;

        const imageUrl = await uploadImageToS3(
          new Blob([imageBuffer]),
          sessionId,
          session.user.id,
          imageIndex,
          pageNumber,
        );
        imageUrls.push(imageUrl);
      }
    }

    // Update session with image URLs (merge with existing data)
    const existingMaterials =
      (sessionData.sourceMaterials as {
        text?: string;
        pdfUrl?: string;
        imageUrls?: string[];
        filename?: string;
        extractedAt?: string;
        numPages?: number;
      }) || {};

    await db
      .update(videoSessions)
      .set({
        sourceMaterials: {
          ...existingMaterials,
          imageUrls: [...(existingMaterials.imageUrls ?? []), ...imageUrls],
          numPages: imageCount > 0 ? imageCount : existingMaterials.numPages,
        },
        updatedAt: new Date(),
      })
      .where(eq(videoSessions.id, sessionId));

    return Response.json({
      success: true,
      sessionId,
      imageCount: imageUrls.length,
      imageUrls,
    });
  } catch (error) {
    console.error("Error uploading images:", error);
    return new Response(
      JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      },
    );
  }
}
