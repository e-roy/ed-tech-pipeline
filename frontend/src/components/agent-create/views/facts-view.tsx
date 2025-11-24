"use client";

import { CheckCircle2, ImageIcon, Loader2 } from "lucide-react";
import type { Fact } from "@/types";
import Image from "next/image";

interface DiagramFile {
  key: string;
  name: string;
  size: number;
  last_modified: string | null;
  content_type: string;
  presigned_url: string;
}

interface FactsViewProps {
  facts: Fact[];
  diagrams?: DiagramFile[];
  isLoadingDiagrams?: boolean;
}

export function FactsView({
  facts,
  diagrams = [],
  isLoadingDiagrams = false,
}: FactsViewProps) {
  return (
    <div className="space-y-6">
      {/* Diagrams Section */}
      {(diagrams.length > 0 || isLoadingDiagrams) && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <ImageIcon className="text-primary size-5" />
            <h2 className="text-lg font-semibold">Relevant Images from PDF</h2>
            {isLoadingDiagrams && (
              <Loader2 className="text-muted-foreground size-4 animate-spin" />
            )}
          </div>

          {isLoadingDiagrams && diagrams.length === 0 ? (
            <div className="text-muted-foreground flex items-center gap-2 rounded-lg border border-dashed p-4 text-sm">
              <Loader2 className="size-4 animate-spin" />
              <span>Analyzing PDF images to find relevant diagrams...</span>
            </div>
          ) : diagrams.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {diagrams.map((diagram, index) => (
                <div
                  key={diagram.key}
                  className="bg-card overflow-hidden rounded-lg border"
                >
                  <div className="relative aspect-video">
                    <Image
                      src={diagram.presigned_url}
                      alt={`Diagram ${index + 1}`}
                      fill
                      className="object-contain"
                      unoptimized // S3 presigned URLs
                    />
                  </div>
                  <div className="border-t p-3">
                    <p className="text-muted-foreground text-xs">
                      {diagram.name.replace(/^diagram_\d+_/, "")}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      )}

      {/* Facts Section */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="text-primary size-5" />
          <h2 className="text-lg font-semibold">Selected Facts</h2>
          <span className="text-muted-foreground text-sm">
            ({facts.length})
          </span>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {facts.map((fact, index) => (
            <div
              key={index}
              className="bg-card border-border rounded-lg border p-4"
            >
              <div className="mb-2 flex items-start justify-between gap-2">
                <h3 className="text-sm font-semibold">{fact.concept}</h3>
                <CheckCircle2 className="text-primary size-4" />
              </div>
              <p className="text-muted-foreground text-sm">{fact.details}</p>
              <div className="text-muted-foreground mt-2 text-xs">
                Confidence:{" "}
                {typeof fact.confidence === "number" &&
                !isNaN(fact.confidence) &&
                fact.confidence >= 0 &&
                fact.confidence <= 1
                  ? `${Math.round(fact.confidence * 100)}%`
                  : "N/A"}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
