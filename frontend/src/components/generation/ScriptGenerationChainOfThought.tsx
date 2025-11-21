"use client";

import { useState, useEffect } from "react";
import { Brain, FileText, PenTool, CheckCircle2 } from "lucide-react";
import {
  ChainOfThought,
  ChainOfThoughtHeader,
  ChainOfThoughtContent,
  ChainOfThoughtStep,
} from "@/components/ai-elements/chain-of-thought";

export function ScriptGenerationChainOfThought({
  isVisible,
  operation = "narrating",
}: {
  isVisible: boolean;
  operation?: "extracting" | "narrating";
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

  const isExtracting = operation === "extracting";

  return (
    <ChainOfThought defaultOpen={true}>
      <ChainOfThoughtHeader>
        {isExtracting ? "Extracting facts" : "Generating your script"}
      </ChainOfThoughtHeader>
      <ChainOfThoughtContent>
        {visibleSteps[0] && (
          <ChainOfThoughtStep
            icon={Brain}
            label={isExtracting ? "Analyzing content" : "Analyzing facts"}
            description={
              isExtracting
                ? "Reading and understanding the provided content"
                : "Reviewing confirmed educational facts and key concepts"
            }
            status="active"
          />
        )}
        {visibleSteps[1] && (
          <ChainOfThoughtStep
            icon={FileText}
            label={
              isExtracting ? "Extracting key facts" : "Structuring narrative"
            }
            description={
              isExtracting
                ? "Identifying key educational concepts and facts"
                : "Organizing content into a coherent educational flow"
            }
            status="active"
          />
        )}
        {visibleSteps[2] && (
          <ChainOfThoughtStep
            icon={isExtracting ? CheckCircle2 : PenTool}
            label={
              isExtracting ? "Validating results" : "Generating script segments"
            }
            description={
              isExtracting
                ? "Validating extracted information for accuracy"
                : "Creating narration and visual guidance for each segment"
            }
            status="active"
          />
        )}
      </ChainOfThoughtContent>
    </ChainOfThought>
  );
}
