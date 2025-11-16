"use client";

import { useFactExtraction } from "@/components/fact-extraction/FactExtractionContext";
import { FactExtractionPanel } from "@/components/fact-extraction/FactExtractionPanel";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { Fact } from "@/types";

function isFact(value: unknown): value is Fact {
  return (
    typeof value === "object" &&
    value !== null &&
    "concept" in value &&
    "details" in value &&
    "confidence" in value
  );
}

export default function CreatePage() {
  const {
    extractedFacts,
    isExtracting,
    extractionError,
    confirmFacts,
    confirmedFacts,
  } = useFactExtraction();

  const handleFactsChange = (_facts: typeof extractedFacts) => {
    // Facts are updated in context - no action needed here
  };

  const handleContinue = (facts: Fact[]) => {
    confirmFacts(facts);
  };

  return (
    <div className="flex h-full flex-col p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Create Educational Video</h1>
        <p className="text-muted-foreground text-sm">
          {confirmedFacts
            ? `Step 2: Generate script (${confirmedFacts.length} facts ready)`
            : "Step 1: Extract facts from your learning materials"}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isExtracting && (
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="border-primary size-5 animate-spin rounded-full border-2 border-t-transparent" />
                <p className="text-muted-foreground">
                  Analyzing your materials and extracting facts...
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {extractionError && (
          <Card>
            <CardContent className="pt-6">
              <p className="text-destructive">{extractionError}</p>
            </CardContent>
          </Card>
        )}

        {extractedFacts.length > 0 && !confirmedFacts && (
          <FactExtractionPanel
            facts={extractedFacts}
            onFactsChange={handleFactsChange}
            onContinue={handleContinue}
          />
        )}

        {confirmedFacts && confirmedFacts.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Facts Confirmed ({confirmedFacts.length})</CardTitle>
              <CardDescription>
                Your facts are ready. Proceed to script generation in Phase 04.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {confirmedFacts.filter(isFact).map((factItem, index) => (
                  <div
                    key={index}
                    className="border-l-primary bg-muted/50 rounded-lg border-l-4 p-3"
                  >
                    <div className="font-semibold">{factItem.concept}</div>
                    <div className="text-muted-foreground text-sm">
                      {factItem.details}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {!isExtracting &&
          extractedFacts.length === 0 &&
          !extractionError &&
          !confirmedFacts && (
            <Card>
              <CardHeader>
                <CardTitle>Ready to Extract Facts</CardTitle>
                <CardDescription>
                  Use the chat panel on the left to provide your learning
                  materials. You can:
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="text-muted-foreground list-disc space-y-2 pl-6">
                  <li>Paste text directly into the chat</li>
                  <li>Upload a PDF file</li>
                  <li>Provide a URL to educational content</li>
                </ul>
              </CardContent>
            </Card>
          )}
      </div>
    </div>
  );
}
