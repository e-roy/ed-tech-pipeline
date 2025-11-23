"use client";

import { CheckCircle2 } from "lucide-react";
import type { Fact } from "@/types";

interface FactsViewProps {
  facts: Fact[];
}

export function FactsView({ facts }: FactsViewProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {facts.map((fact, index) => (
        <div
          key={index}
          className="border-border bg-card rounded-lg border p-4"
        >
          <div className="mb-2 flex items-start justify-between gap-2">
            <h3 className="text-sm font-semibold">{fact.concept}</h3>
            <CheckCircle2 className="text-primary size-4" />
          </div>
          <p className="text-muted-foreground text-sm">{fact.details}</p>
          <div className="text-muted-foreground mt-2 text-xs">
            Confidence: {Math.round(fact.confidence * 100)}%
          </div>
        </div>
      ))}
    </div>
  );
}

