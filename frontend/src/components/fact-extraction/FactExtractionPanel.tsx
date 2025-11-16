"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { Fact } from "@/types";
import { Trash2, Plus } from "lucide-react";

interface FactExtractionPanelProps {
  facts: Fact[];
  onFactsChange: (facts: Fact[]) => void;
  onContinue: (facts: Fact[]) => void;
}

export function FactExtractionPanel({
  facts,
  onFactsChange,
  onContinue,
}: FactExtractionPanelProps) {
  const [localFacts, setLocalFacts] = useState<Fact[]>(facts);

  const updateFact = (index: number, updates: Partial<Fact>) => {
    const updated = [...localFacts];
    updated[index] = { ...updated[index], ...updates } as Fact;
    setLocalFacts(updated);
    onFactsChange(updated);
  };

  const deleteFact = (index: number) => {
    const updated = localFacts.filter((_, i) => i !== index);
    setLocalFacts(updated);
    onFactsChange(updated);
  };

  const addFact = () => {
    const newFact: Fact = {
      concept: "",
      details: "",
      confidence: 1.0,
    } as Fact;
    const updated = [...localFacts, newFact];
    setLocalFacts(updated);
    onFactsChange(updated);
  };

  const handleContinue = () => {
    // Filter out empty facts before continuing
    const validFacts = localFacts.filter(
      (fact) => fact.concept.trim() !== "" && fact.details.trim() !== "",
    );
    if (validFacts.length === 0) {
      alert("Please add at least one fact before continuing.");
      return;
    }
    onFactsChange(validFacts);
    onContinue(validFacts);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Extracted Facts ({localFacts.length})</CardTitle>
        <CardDescription>
          Review and edit the extracted facts. You can add, edit, or remove
          facts before continuing.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3">
          {localFacts.map((fact, index) => (
            <div
              key={index}
              className="border-l-primary bg-muted/50 flex gap-3 rounded-lg border-l-4 p-4"
            >
              <div className="flex-1 space-y-2">
                <Input
                  value={fact.concept}
                  onChange={(e) =>
                    updateFact(index, { concept: e.target.value })
                  }
                  placeholder="Concept (e.g., Photosynthesis)"
                  className="font-semibold"
                />
                <Textarea
                  value={fact.details}
                  onChange={(e) =>
                    updateFact(index, { details: e.target.value })
                  }
                  placeholder="Details about this concept..."
                  rows={2}
                  className="text-sm"
                />
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => deleteFact(index)}
                className="text-destructive hover:text-destructive shrink-0"
              >
                <Trash2 className="size-4" />
              </Button>
            </div>
          ))}
        </div>

        <div className="flex gap-2">
          <Button variant="outline" onClick={addFact} className="w-full">
            <Plus className="mr-2 size-4" />
            Add Fact
          </Button>
        </div>

        <div className="flex justify-end gap-2 pt-4">
          <Button onClick={handleContinue} className="min-w-32">
            Continue to Script Generation →
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
