// Import UIMessage from ai package
import type { UIMessage } from "ai";

// Re-export for convenience
export type AIMessage = UIMessage;

/**
 * Image data structure returned from the backend API
 */
export interface ImageData {
  url: string;
  index: number;
}

/**
 * Extended message data that can be stored in the AI SDK Message's data field
 */
export interface ChatMessageData {
  images?: ImageData[];
}

/**
 * Type for messages with image data
 */
export type MessageWithImages = AIMessage & {
  data?: ChatMessageData;
};

/**
 * Type guard to check if a message has image data
 */
export function hasImageData(message: AIMessage): message is MessageWithImages {
  // Check if message has data parts with images
  // Data parts have type like "data-${string}"
  const dataPart = message.parts?.find(
    (part): part is { type: `data-${string}`; data: unknown } =>
      part.type.startsWith("data-") && "data" in part,
  );
  if (!dataPart) return false;

  const data = dataPart.data as ChatMessageData | undefined;
  return (
    data !== undefined &&
    typeof data === "object" &&
    data !== null &&
    "images" in data &&
    Array.isArray(data.images)
  );
}

/**
 * Extract images from a message if they exist
 */
export function getImagesFromMessage(
  message: AIMessage,
): ImageData[] | undefined {
  // Find data part with images
  // Data parts have type like "data-${string}"
  const dataPart = message.parts?.find(
    (part): part is { type: `data-${string}`; data: unknown } =>
      part.type.startsWith("data-") && "data" in part,
  );
  if (!dataPart) return undefined;

  const data = dataPart.data as ChatMessageData | undefined;
  return data?.images;
}
