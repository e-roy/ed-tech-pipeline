/**
 * AI utility functions for parsing and processing AI responses
 */

/**
 * Safely parses a tool result that may be a string or object
 */
export function parseToolResult<T>(toolResult: unknown): T {
  return typeof toolResult === "string"
    ? (JSON.parse(toolResult) as T)
    : (toolResult as T);
}
