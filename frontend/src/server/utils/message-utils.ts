import { nanoid } from "nanoid";
import { db } from "@/server/db";
import { conversationMessages } from "@/server/db/video-generation/schema";
import type { ModelMessage } from "ai";
import type { UIMessage } from "ai";
import { eq, asc } from "drizzle-orm";

/**
 * Extract text content from a message.
 * Handles both ModelMessage and UIMessage formats.
 */
function extractMessageContent(message: ModelMessage | UIMessage): string {
  // Check if it's a ModelMessage (has content property)
  if ("content" in message) {
    if (typeof message.content === "string") {
      return message.content;
    }

    // Handle ModelMessage with array content
    if (Array.isArray(message.content)) {
      return message.content
        .map((part) => {
          if (typeof part === "string") return part;
          if (typeof part === "object" && part !== null && "type" in part) {
            if (part.type === "text" && "text" in part) {
              return typeof part.text === "string" ? part.text : "";
            }
          }
          return "";
        })
        .join("");
    }
  }

  // Handle UIMessage (has parts property)
  if ("parts" in message && message.parts) {
    return message.parts
      .map((part) => {
        if (typeof part === "object" && part !== null && "type" in part) {
          if (part.type === "text" && "text" in part) {
            return typeof part.text === "string" ? part.text : "";
          }
        }
        return "";
      })
      .join("");
  }

  return "";
}

/**
 * Extract parts structure from UIMessage (for file attachments, etc.)
 */
function extractMessageParts(message: ModelMessage | UIMessage): unknown {
  // UIMessage has parts property
  if ("parts" in message && message.parts) {
    return message.parts;
  }

  // ModelMessage content might be an array
  if ("content" in message && Array.isArray(message.content)) {
    return message.content;
  }

  return null;
}

/**
 * Save a single conversation message to the database.
 */
export async function saveConversationMessage(
  sessionId: string,
  message: ModelMessage | UIMessage,
  metadata?: Record<string, unknown>,
): Promise<string> {
  const messageId = nanoid();
  const content = extractMessageContent(message);
  const parts = extractMessageParts(message);

  // Determine role - handle both formats
  const role =
    message.role === "user" ||
    message.role === "assistant" ||
    message.role === "system"
      ? message.role
      : "user";

  await db.insert(conversationMessages).values({
    id: messageId,
    sessionId,
    role,
    content,
    parts: parts ? (parts as unknown) : null,
    metadata: metadata ?? null,
    createdAt: new Date(),
  });

  return messageId;
}

/**
 * Save multiple conversation messages to the database.
 * Useful for saving the entire conversation history.
 */
export async function saveConversationMessages(
  sessionId: string,
  messages: (ModelMessage | UIMessage)[],
  metadata?: Record<string, unknown>,
): Promise<string[]> {
  const messageIds: string[] = [];

  for (const message of messages) {
    const id = await saveConversationMessage(sessionId, message, metadata);
    messageIds.push(id);
  }

  return messageIds;
}

/**
 * Save assistant response after streaming completes.
 * This is designed to be called from onFinish callbacks.
 */
export async function saveAssistantResponse(
  sessionId: string,
  content: string,
  metadata?: {
    mode?: string;
    objectId?: string;
    [key: string]: unknown;
  },
): Promise<string> {
  return saveConversationMessage(
    sessionId,
    {
      role: "assistant",
      content,
    },
    metadata,
  );
}

/**
 * Load all conversation messages for a session from the database.
 * Returns messages ordered by creation time.
 */
export async function loadConversationMessages(
  sessionId: string,
): Promise<ModelMessage[]> {
  const dbMessages = await db
    .select()
    .from(conversationMessages)
    .where(eq(conversationMessages.sessionId, sessionId))
    .orderBy(asc(conversationMessages.createdAt));

  return dbMessages.map((msg): ModelMessage => {
    // Use content as primary, or reconstruct from parts if content is empty
    const content: ModelMessage["content"] =
      msg.content ||
      (msg.parts
        ? (msg.parts as ModelMessage["content"])
        : ("" as ModelMessage["content"]));

    const role = msg.role as "user" | "assistant" | "system";

    // Create message with proper typing
    if (role === "user") {
      return {
        role: "user",
        content,
      } as ModelMessage;
    } else if (role === "assistant") {
      return {
        role: "assistant",
        content,
      } as ModelMessage;
    } else {
      return {
        role: "system",
        content,
      } as ModelMessage;
    }
  });
}

/**
 * Save only new conversation messages that haven't been saved yet.
 * Compares message content with existing DB messages to avoid duplicates.
 */
export async function saveNewConversationMessages(
  sessionId: string,
  messages: (ModelMessage | UIMessage)[],
  metadata?: Record<string, unknown>,
): Promise<string[]> {
  // Load existing messages from DB to check for duplicates
  const existingMessages = await db
    .select()
    .from(conversationMessages)
    .where(eq(conversationMessages.sessionId, sessionId))
    .orderBy(asc(conversationMessages.createdAt));

  // Create a set of existing message content for quick lookup
  // Use role:content as the key to identify duplicates
  const existingContents = new Set(
    existingMessages.map((m) => `${m.role}:${m.content}`),
  );

  const messageIds: string[] = [];

  for (const message of messages) {
    const content = extractMessageContent(message);
    const role =
      message.role === "user" ||
      message.role === "assistant" ||
      message.role === "system"
        ? message.role
        : "user";
    const key = `${role}:${content}`;

    // Skip if message already exists
    if (existingContents.has(key)) {
      continue;
    }

    // Save new message
    const id = await saveConversationMessage(sessionId, message, metadata);
    messageIds.push(id);
    existingContents.add(key); // Track to avoid duplicates in same batch
  }

  return messageIds;
}
