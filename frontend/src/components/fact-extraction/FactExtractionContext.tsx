"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import type { Fact } from "@/types";

export interface FactExtractionContextValue {
  extractedFacts: Fact[];
  isExtracting: boolean;
  extractionError: string | null;
  extractFactsFromInput: (text: string, files: File[]) => Promise<void>;
  setExtractedFacts: (facts: Fact[]) => void;
  setIsExtracting: (isExtracting: boolean) => void;
  clearFacts: () => void;
  confirmFacts: (facts: Fact[]) => void;
  confirmedFacts: Fact[] | null;
}

const FactExtractionContext = createContext<
  FactExtractionContextValue | undefined
>(undefined);

export function FactExtractionProvider({ children }: { children: ReactNode }) {
  const [extractedFacts, setExtractedFacts] = useState<Fact[]>([]);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  const [confirmedFacts, setConfirmedFacts] = useState<Fact[] | null>(null);

  const extractFactsFromInput = useCallback(
    async (text: string, files: File[]) => {
      setIsExtracting(true);
      setExtractionError(null);

      try {
        // Dynamic imports to avoid SSR issues
        const [{ extractTextFromPDF }, { extractFacts }, { fetchURLContent }] =
          await Promise.all([
            import("@/lib/extractPDF"),
            import("@/lib/extractFacts"),
            import("@/lib/fetchURL"),
          ]);

        let combinedText = text;

        // Extract text from PDF files
        for (const file of files) {
          if (file.type === "application/pdf") {
            try {
              const pdfText = await extractTextFromPDF(file);
              combinedText += "\n\n" + pdfText;
            } catch (error) {
              console.error("Error extracting PDF:", error);
            }
          }
        }

        // Extract text from URL if present
        const urlPattern =
          /(https?:\/\/[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s]*)/;
        const urlMatch = urlPattern.exec(text);
        if (urlMatch?.[0]) {
          try {
            const urlText = await fetchURLContent(urlMatch[0]);
            combinedText += "\n\n" + urlText;
          } catch (error) {
            console.error("Error fetching URL:", error);
          }
        }

        // Extract facts from combined text
        if (combinedText.trim()) {
          const facts = extractFacts(combinedText);
          setExtractedFacts(facts);
        } else {
          setExtractionError("No text content found to extract facts from.");
        }
      } catch (error) {
        console.error("Error during fact extraction:", error);
        setExtractionError(
          error instanceof Error
            ? error.message
            : "Failed to extract facts. Please try again.",
        );
      } finally {
        setIsExtracting(false);
      }
    },
    [],
  );

  const setExtractedFactsFromContext = useCallback((facts: Fact[]) => {
    setExtractedFacts(facts);
    setExtractionError(null);
    setIsExtracting(false); // Stop loading when facts are set
  }, []);

  const setIsExtractingFromContext = useCallback((extracting: boolean) => {
    setIsExtracting(extracting);
  }, []);

  const clearFacts = useCallback(() => {
    setExtractedFacts([]);
    setExtractionError(null);
  }, []);

  const confirmFacts = useCallback((facts: Fact[]) => {
    setConfirmedFacts(facts);
    // Store in localStorage
    localStorage.setItem("facts_current", JSON.stringify(facts));
  }, []);

  return (
    <FactExtractionContext.Provider
      value={{
        extractedFacts,
        isExtracting,
        extractionError,
        extractFactsFromInput,
        setExtractedFacts: setExtractedFactsFromContext,
        setIsExtracting: setIsExtractingFromContext,
        clearFacts,
        confirmFacts,
        confirmedFacts,
      }}
    >
      {children}
    </FactExtractionContext.Provider>
  );
}

export function useFactExtraction() {
  const context = useContext(FactExtractionContext);
  if (context === undefined) {
    throw new Error(
      "useFactExtraction must be used within a FactExtractionProvider",
    );
  }
  return context;
}
