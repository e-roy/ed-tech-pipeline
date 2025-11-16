import type { Fact } from "@/types";

/**
 * Parses facts from an AI message response.
 * Looks for JSON code blocks or standalone JSON objects containing facts.
 *
 * @param text - The message text to parse
 * @returns Array of parsed facts, or null if no facts found
 */
export function parseFactsFromMessage(text: string): Fact[] | null {
  try {
    // Look for JSON code block
    const jsonPattern = /```json\s*([\s\S]*?)\s*```/;
    const jsonMatch = jsonPattern.exec(text);
    if (jsonMatch?.[1]) {
      const parsed = JSON.parse(jsonMatch[1]) as {
        facts?: Array<{
          concept?: unknown;
          details?: unknown;
          confidence?: unknown;
        }>;
      };
      if (parsed.facts && Array.isArray(parsed.facts)) {
        return parsed.facts
          .filter(
            (
              fact,
            ): fact is {
              concept?: unknown;
              details?: unknown;
              confidence?: unknown;
            } => fact !== null && typeof fact === "object",
          )
          .map((fact) => {
            const concept =
              typeof fact.concept === "string"
                ? fact.concept
                : typeof fact.concept === "number"
                  ? String(fact.concept)
                  : "";
            const details =
              typeof fact.details === "string"
                ? fact.details
                : typeof fact.details === "number"
                  ? String(fact.details)
                  : "";
            return {
              concept: concept.trim(),
              details: details.trim(),
              confidence:
                typeof fact.confidence === "number" ? fact.confidence : 0.8,
            };
          })
          .filter(
            (fact): fact is Fact =>
              fact.concept !== "" && fact.details !== "",
          );
      }
    }
    // Also try to find JSON object directly
    const jsonObjPattern = /\{[\s\S]*"facts"[\s\S]*\}/;
    const jsonObjMatch = jsonObjPattern.exec(text);
    if (jsonObjMatch?.[0]) {
      const parsed = JSON.parse(jsonObjMatch[0]) as {
        facts?: Array<{
          concept?: unknown;
          details?: unknown;
          confidence?: unknown;
        }>;
      };
      if (parsed.facts && Array.isArray(parsed.facts)) {
        return parsed.facts
          .filter(
            (
              fact,
            ): fact is {
              concept?: unknown;
              details?: unknown;
              confidence?: unknown;
            } => fact !== null && typeof fact === "object",
          )
          .map((fact) => {
            const concept =
              typeof fact.concept === "string"
                ? fact.concept
                : typeof fact.concept === "number"
                  ? String(fact.concept)
                  : "";
            const details =
              typeof fact.details === "string"
                ? fact.details
                : typeof fact.details === "number"
                  ? String(fact.details)
                  : "";
            return {
              concept: concept.trim(),
              details: details.trim(),
              confidence:
                typeof fact.confidence === "number" ? fact.confidence : 0.8,
            };
          })
          .filter(
            (fact): fact is Fact =>
              fact.concept !== "" && fact.details !== "",
          );
      }
    }
  } catch (error) {
    console.error("Error parsing facts from message:", error);
  }
  return null;
}

