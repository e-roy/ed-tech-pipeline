"use server";

import { listDirectoryStructure } from "@/server/services/storage";
import type { DirectoryData } from "@/components/hardcode-assets/types";

/**
 * Server action to load folder contents for lazy loading.
 * Extracts the prefix from the folder path and calls listDirectoryStructure.
 */
export async function loadFolderContents(
  userId: string,
  folderPath: string,
): Promise<DirectoryData> {
  // Extract prefix from folder path (remove users/{userId}/)
  const basePrefix = `users/${userId}/`;
  if (!folderPath.startsWith(basePrefix)) {
    throw new Error("Invalid folder path");
  }

  const prefix = folderPath.slice(basePrefix.length);
  const result = await listDirectoryStructure(userId, prefix);

  return result;
}
