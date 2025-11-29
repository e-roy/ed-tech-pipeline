import type { FileUIPart } from "ai";

interface PdfUploadResult {
  s3FileParts: FileUIPart[];
  sessionId?: string;
}

interface PdfUploadOptions {
  files: FileUIPart[];
  currentSessionId?: string | null;
  onSessionIdCreated?: (sessionId: string) => void;
}

/**
 * Processes PDF files: extracts text, uploads to S3, and backgrounds image extraction
 */
export async function processPdfUploads({
  files,
  currentSessionId,
  onSessionIdCreated,
}: PdfUploadOptions): Promise<PdfUploadResult> {
  const s3FileParts: FileUIPart[] = [];
  let newSessionId: string | undefined;

  for (const filePart of files) {
    if (filePart.mediaType !== "application/pdf") continue;

    try {
      // Fetch and convert blob to File
      const response = await fetch(filePart.url);
      const blob = await response.blob();
      const file = new File(
        [blob],
        filePart.filename ?? "document.pdf",
        { type: "application/pdf" },
      );

      // Extract text immediately
      const { extractTextFromPDF } = await import("@/lib/extractPDF");
      const pdfText = await extractTextFromPDF(file);

      // Upload PDF to S3
      const formData = new FormData();
      formData.append("pdf", file);
      if (currentSessionId) {
        formData.append("sessionId", currentSessionId);
      }
      formData.append("extractedText", pdfText);
      formData.append("imageCount", "0");

      const uploadResponse = await fetch(
        "/api/agent-create/session/upload-pdf",
        {
          method: "POST",
          body: formData,
        },
      );

      if (!uploadResponse.ok) {
        console.error("Failed to upload PDF:", await uploadResponse.text());
        continue;
      }

      const uploadData = (await uploadResponse.json()) as {
        sessionId: string;
        pdfUrl: string;
        imageCount: number;
      };

      // Track sessionId if it was just created
      if (uploadData.sessionId && !currentSessionId) {
        newSessionId = uploadData.sessionId;
        onSessionIdCreated?.(uploadData.sessionId);
      }

      // Create FileUIPart with S3 URL (not blob URL)
      s3FileParts.push({
        type: "file",
        mediaType: "application/pdf",
        filename: filePart.filename,
        url: uploadData.pdfUrl, // S3 URL, accessible by server
      });

      if (process.env.NODE_ENV === "development") {
        console.log(`PDF uploaded to S3: ${uploadData.pdfUrl}`);
      }

      // Extract and upload images in background (non-blocking)
      void backgroundExtractImages(file, uploadData.sessionId);
    } catch (error) {
      console.error("Error processing PDF:", error);
    }
  }

  return { s3FileParts, sessionId: newSessionId };
}

/**
 * Background task: Extract images from PDF and upload them
 */
async function backgroundExtractImages(
  file: File,
  sessionId: string,
): Promise<void> {
  try {
    const { extractImagesFromPdf } = await import("@/lib/pdf-image-extractor");
    const extractedImages = await extractImagesFromPdf(file);

    if (extractedImages.length > 0) {
      const imageFormData = new FormData();
      imageFormData.append("sessionId", sessionId);
      imageFormData.append("imageCount", extractedImages.length.toString());

      extractedImages.forEach((img, index) => {
        const filename = `page_${img.pageNumber}_img_${img.imageIndex}.png`;
        const imageFile = new File([img.blob], filename, {
          type: "image/png",
        });
        imageFormData.append(`image_${index}`, imageFile);
      });

      await fetch("/api/agent-create/session/upload-images", {
        method: "POST",
        body: imageFormData,
      });
    }
  } catch (error) {
    console.error("Background image extraction failed:", error);
  }
}

