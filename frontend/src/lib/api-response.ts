import type { Fact, Narration } from "@/types";

export interface StandardApiResponse {
  success: boolean;
  facts?: Fact[];
  narration?: Narration;
  message?: string;
  topic?: string;
  learningObjective?: string;
  childAge?: string;
  childInterest?: string;
  error?: string;
}

/**
 * Unwraps AI SDK tool result wrapper and parses JSON strings
 */
export function unwrapToolResult(toolResult: unknown): Record<string, unknown> {
  let actualResult = toolResult;

  // Unwrap AI SDK wrapper if present
  if (typeof toolResult === "object" && toolResult !== null) {
    const wrapped = toolResult as { output?: unknown; type?: string };
    if (wrapped.type === "tool-result" && wrapped.output !== undefined) {
      actualResult = wrapped.output;
    }
  }

  // Parse JSON string if needed
  if (typeof actualResult === "string") {
    try {
      return JSON.parse(actualResult) as Record<string, unknown>;
    } catch {
      return { message: actualResult };
    }
  }

  return (actualResult as Record<string, unknown>) ?? {};
}

/**
 * Builds standardized API response from tool result
 */
export function buildStandardResponse(
  toolResult: unknown,
  defaultMessage = "Operation completed",
): StandardApiResponse {
  const data = unwrapToolResult(toolResult);
  return {
    success: data.success !== false,
    facts: data.facts as Fact[] | undefined,
    narration: data.narration as Narration | undefined,
    message: (data.message as string) ?? defaultMessage,
    topic: data.topic as string | undefined,
    learningObjective: data.learningObjective as string | undefined,
    childAge: data.child_age as string | undefined,
    childInterest: data.child_interest as string | undefined,
    error: data.error as string | undefined,
  };
}

