"use client";

import { useState, useEffect } from "react";
import { FileText, Search, Brain } from "lucide-react";
import {
  ChainOfThought,
  ChainOfThoughtHeader,
  ChainOfThoughtContent,
  ChainOfThoughtStep,
} from "@/components/ai-elements/chain-of-thought";

export function FactExtractionChainOfThought({
  isVisible,
}: {
  isVisible: boolean;
}) {
  const [visibleSteps, setVisibleSteps] = useState<boolean[]>([
    false,
    false,
    false,
  ]);

  useEffect(() => {
    if (!isVisible) {
      setVisibleSteps([false, false, false]);
      return;
    }

    // Reset and show steps progressively
    setVisibleSteps([false, false, false]);

    const timers: NodeJS.Timeout[] = [];

    // Show first step after delay
    timers.push(
      setTimeout(() => {
        setVisibleSteps([true, false, false]);
      }, 2000),
    );

    // Show second step after delay
    timers.push(
      setTimeout(() => {
        setVisibleSteps([true, true, false]);
      }, 4500),
    );

    // Show third step after another delay
    timers.push(
      setTimeout(() => {
        setVisibleSteps([true, true, true]);
      }, 8000),
    );

    return () => {
      timers.forEach((timer) => clearTimeout(timer));
    };
  }, [isVisible]);

  return (
    <ChainOfThought defaultOpen={true}>
      <ChainOfThoughtHeader>Processing your materials</ChainOfThoughtHeader>
      <ChainOfThoughtContent>
        {visibleSteps[0] && (
          <ChainOfThoughtStep
            icon={FileText}
            label="Reading materials"
            description="Extracting text from PDFs and URLs"
            status="active"
          />
        )}
        {visibleSteps[1] && (
          <ChainOfThoughtStep
            icon={Search}
            label="Analyzing content"
            description="Processing with AI to understand key concepts"
            status="active"
          />
        )}
        {visibleSteps[2] && (
          <ChainOfThoughtStep
            icon={Brain}
            label="Identifying facts"
            description="Extracting educational facts from materials"
            status="active"
          />
        )}
      </ChainOfThoughtContent>
    </ChainOfThought>
  );
}
