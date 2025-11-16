import { useCallback } from "react";
import type { FileUIPart } from "ai";
import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import { useFactExtraction } from "@/components/fact-extraction/FactExtractionContext";

/**
 * Custom hook for handling fact extraction submit logic.
 * Extracts content from PDFs and URLs, prepares the message for AI processing.
 */
export function useFactExtractionSubmit() {
  const factExtraction = useFactExtraction();

  const handleFactExtractionSubmit = useCallback(
    async (
      message: PromptInputMessage,
      sendMessage: (message: {
        role: "user";
        parts: Array<{ type: "text"; text: string } | FileUIPart>;
      }) => Promise<void>,
    ) => {
      if (!message.text.trim() && message.files.length === 0) return;

      // Keep user's original message for display
      const userMessageText = message.text.trim();
      const nonPdfFiles: FileUIPart[] = [];

      // Extract content from PDFs and URLs (for AI, not for display)
      const extractedContent: string[] = [];

      // Extract text from PDFs
      for (const filePart of message.files) {
        if (filePart.mediaType === "application/pdf") {
          try {
            // Extract text from PDF
            const response = await fetch(filePart.url);
            const blob = await response.blob();
            const file = new File([blob], filePart.filename ?? "document.pdf", {
              type: "application/pdf",
            });

            const { extractTextFromPDF } = await import("@/lib/extractPDF");
            const pdfText = await extractTextFromPDF(file);
            extractedContent.push(
              `--- Content from ${filePart.filename ?? "PDF"} ---\n${pdfText}`,
            );
          } catch (error) {
            console.error("Error extracting PDF text:", error);
            // If PDF extraction fails, include the file anyway
            nonPdfFiles.push(filePart);
          }
        } else {
          nonPdfFiles.push(filePart);
        }
      }

      // Extract text from URLs in the message
      // Match URLs more precisely to avoid false positives
      const urlPattern =
        /(https?:\/\/[^\s<>"']+|www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s<>"']*)/;
      const urlMatch = urlPattern.exec(userMessageText);
      if (urlMatch?.[0]) {
        try {
          const { fetchURLContent } = await import("@/lib/fetchURL");
          const urlText = await fetchURLContent(urlMatch[0]);
          if (urlText && urlText.trim().length > 0) {
            extractedContent.push(
              `--- Content from ${urlMatch[0]} ---\n${urlText}`,
            );
          }
        } catch (error) {
          // If URL fetching fails, just include the URL in the text
          // The AI can still reference it even if we couldn't fetch the content
          console.warn(
            "Could not fetch URL content, will include URL in message:",
            error,
          );
          // Don't add anything - the URL is already in userMessageText
        }
      }

      // Build message for AI: user's text + extracted content
      // Display only shows user's original message
      let messageForAI = userMessageText;

      // Add extracted content if available
      if (extractedContent.length > 0) {
        messageForAI += `\n\n--- Extracted Learning Materials (for fact extraction) ---\n${extractedContent.join("\n\n")}`;
      }

      // If user hasn't provided structured info, help them format it
      if (
        messageForAI &&
        !messageForAI.toLowerCase().includes("topic:") &&
        !messageForAI.toLowerCase().includes("learning objective:")
      ) {
        messageForAI = `Please extract educational facts from the following materials:\n\n${messageForAI}`;
      } else if (!messageForAI && nonPdfFiles.length > 0) {
        messageForAI =
          "Please extract educational facts from the attached materials.";
      }

      // Set extracting state to show loading in main content
      factExtraction.setIsExtracting?.(true);

      // Send message to AI agent with full content
      // The displayed message will be the user's original text
      await sendMessage({
        role: "user",
        parts: [
          ...(messageForAI
            ? [{ type: "text" as const, text: messageForAI }]
            : []),
          ...nonPdfFiles,
        ],
      });
    },
    [factExtraction],
  );

  return { handleFactExtractionSubmit };
}

