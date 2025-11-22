/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/**
 * Storage service for S3 file operations.
 * Direct S3 access without going through FastAPI backend.
 */

import {
  S3Client,
  ListObjectsV2Command,
  DeleteObjectCommand,
  GetObjectCommand,
} from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { env } from "@/env";
import { db } from "@/server/db";
import { videoAssets, videoSessions } from "@/server/db/schema";
import { eq } from "drizzle-orm";

// Initialize S3 client (only if credentials are provided)
let s3Client: S3Client | null = null;

function getS3Client(): S3Client {
  if (!s3Client) {
    if (!env.AWS_ACCESS_KEY_ID || !env.AWS_SECRET_ACCESS_KEY) {
      throw new Error(
        "AWS credentials not configured. Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and S3_BUCKET_NAME in .env",
      );
    }

    s3Client = new S3Client({
      region: env.AWS_REGION,
      credentials: {
        accessKeyId: env.AWS_ACCESS_KEY_ID,
        secretAccessKey: env.AWS_SECRET_ACCESS_KEY,
      },
    });
  }
  return s3Client;
}

/**
 * Infer content type from file extension.
 */
function getContentTypeFromKey(key: string): string {
  const ext = key.split(".").pop()?.toLowerCase();
  const contentTypes: Record<string, string> = {
    // Images
    jpg: "image/jpeg",
    jpeg: "image/jpeg",
    png: "image/png",
    gif: "image/gif",
    webp: "image/webp",
    svg: "image/svg+xml",
    // Videos
    mp4: "video/mp4",
    webm: "video/webm",
    mov: "video/quicktime",
    avi: "video/x-msvideo",
    // Audio
    mp3: "audio/mpeg",
    wav: "audio/wav",
    ogg: "audio/ogg",
    // Documents
    pdf: "application/pdf",
    doc: "application/msword",
    docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    // Text
    txt: "text/plain",
    md: "text/markdown",
    json: "application/json",
    // Other
    zip: "application/zip",
  };
  return ext
    ? (contentTypes[ext] ?? "application/octet-stream")
    : "application/octet-stream";
}

/**
 * List files in user's S3 folder.
 */
export async function listUserFiles(
  userId: string,
  folder: "input" | "output",
  options: {
    asset_type?: "images" | "videos" | "audio" | "final";
    limit?: number;
    offset?: number;
  } = {},
): Promise<{
  files: Array<{
    key: string;
    size: number;
    last_modified: string | null;
    content_type: string;
    presigned_url: string;
  }>;
  total: number;
  limit: number;
  offset: number;
}> {
  const { asset_type, limit = 100, offset = 0 } = options;

  if (!env.S3_BUCKET_NAME) {
    throw new Error("S3_BUCKET_NAME not configured");
  }

  const client = getS3Client();
  const allObjects: Array<{
    Key: string;
    Size: number;
    LastModified?: Date;
    ContentType?: string;
  }> = [];

  if (folder === "input") {
    // List input folder files
    const prefix = `users/${userId}/input/`;
    let continuationToken: string | undefined;
    do {
      const command = new ListObjectsV2Command({
        Bucket: env.S3_BUCKET_NAME,
        Prefix: prefix,
        MaxKeys: limit + offset,
        ContinuationToken: continuationToken,
      });

      const response = await client.send(command);
      if (response.Contents) {
        const validObjects = response.Contents.filter(
          (obj): obj is typeof obj & { Key: string } => !!obj.Key,
        ).map((obj) => ({
          Key: obj.Key,
          Size: obj.Size ?? 0,
          LastModified: obj.LastModified,
          ContentType: undefined, // ListObjectsV2 doesn't return ContentType
        }));
        allObjects.push(...validObjects);
      }
      continuationToken = response.NextContinuationToken;
    } while (continuationToken);
  } else {
    // For output folder, list all files from session folders: users/{userId}/{sessionId}/
    // List all session folders under user prefix
    const userPrefix = `users/${userId}/`;
    const sessionFolders: string[] = [];

    // List all session folders (users/{userId}/{session_id}/)
    // Exclude 'input' folder as it's not part of session output
    let continuationToken: string | undefined;
    do {
      const command = new ListObjectsV2Command({
        Bucket: env.S3_BUCKET_NAME,
        Prefix: userPrefix,
        Delimiter: "/",
        MaxKeys: 1000,
        ContinuationToken: continuationToken,
      });

      const response = await client.send(command);

      // Collect session folder prefixes
      if (response.CommonPrefixes) {
        for (const prefix of response.CommonPrefixes) {
          if (prefix.Prefix) {
            // Match session folders: users/{userId}/{sessionId}/
            // userId is a UUID string, not a number
            // Exclude 'input' and 'output' folders
            const sessionIdRegex = /^users\/[^/]+\/([^/]+)\/$/;
            const sessionIdMatch = sessionIdRegex.exec(prefix.Prefix);
            if (sessionIdMatch) {
              const folderName = sessionIdMatch[1];
              // Exclude 'input' and 'output' folders, include all other session folders
              if (folderName !== "input" && folderName !== "output") {
                sessionFolders.push(prefix.Prefix);
              }
            }
          }
        }
      }

      continuationToken = response.NextContinuationToken;
    } while (continuationToken);

    // List all files directly from each session folder (files are in users/{userId}/{sessionId}/, not in subfolders)
    for (const sessionPrefix of sessionFolders) {
      let sessionContinuationToken: string | undefined;
      do {
        const command = new ListObjectsV2Command({
          Bucket: env.S3_BUCKET_NAME,
          Prefix: sessionPrefix,
          MaxKeys: 1000,
          ContinuationToken: sessionContinuationToken,
        });

        const response = await client.send(command);
        if (response.Contents) {
          const validObjects = response.Contents.filter(
            (obj): obj is typeof obj & { Key: string } => !!obj.Key,
          )
            .filter((obj) => {
              // Exclude directory markers and metadata files
              const key = obj.Key;
              return (
                !key.endsWith("/") &&
                !key.endsWith("segments.md") &&
                !key.endsWith("status.json") &&
                !key.endsWith("diagram.png")
              );
            })
            .map((obj) => ({
              Key: obj.Key,
              Size: obj.Size ?? 0,
              LastModified: obj.LastModified,
              ContentType: undefined, // ListObjectsV2 doesn't return ContentType
            }));
          allObjects.push(...validObjects);
        }
        sessionContinuationToken = response.NextContinuationToken;
      } while (sessionContinuationToken);
    }
  }

  // Filter out directory markers and apply pagination
  const files = allObjects
    .filter((obj) => !obj.Key.endsWith("/"))
    .slice(offset, offset + limit);

  // Generate presigned URLs for each file
  const filesWithUrls = await Promise.all(
    files.map(async (obj) => {
      const key = obj.Key;
      const presignedUrl = await getSignedUrl(
        client,
        new GetObjectCommand({
          Bucket: env.S3_BUCKET_NAME,
          Key: key,
        }),
        { expiresIn: 3600 }, // 1 hour
      );

      return {
        key,
        size: obj.Size ?? 0,
        last_modified: obj.LastModified?.toISOString() ?? null,
        content_type: getContentTypeFromKey(key),
        presigned_url: presignedUrl,
      };
    }),
  );

  return {
    files: filesWithUrls,
    total: allObjects.filter((obj) => obj.Key && !obj.Key.endsWith("/")).length,
    limit,
    offset,
  };
}

/**
 * Delete a file from S3.
 */
export async function deleteUserFile(
  userId: string,
  fileKey: string,
): Promise<{ status: string; message: string; key: string }> {
  if (!env.S3_BUCKET_NAME) {
    throw new Error("S3_BUCKET_NAME not configured");
  }

  // Verify the file belongs to the user
  const expectedPrefix = `users/${userId}/`;
  if (!fileKey.startsWith(expectedPrefix)) {
    throw new Error("File does not belong to user");
  }

  const client = getS3Client();
  await client.send(
    new DeleteObjectCommand({
      Bucket: env.S3_BUCKET_NAME,
      Key: fileKey,
    }),
  );

  return {
    status: "success",
    message: "File deleted successfully",
    key: fileKey,
  };
}

/**
 * Get a presigned URL for a file.
 */
export async function getPresignedUrl(
  userId: string,
  fileKey: string,
  expiresIn = 3600,
): Promise<{ presigned_url: string; expires_in: number }> {
  if (!env.S3_BUCKET_NAME) {
    throw new Error("S3_BUCKET_NAME not configured");
  }

  // Verify the file belongs to the user
  const expectedPrefix = `users/${userId}/`;
  if (!fileKey.startsWith(expectedPrefix)) {
    throw new Error("File does not belong to user");
  }

  const client = getS3Client();
  const presignedUrl = await getSignedUrl(
    client,
    new GetObjectCommand({
      Bucket: env.S3_BUCKET_NAME,
      Key: fileKey,
    }),
    { expiresIn },
  );

  return {
    presigned_url: presignedUrl,
    expires_in: expiresIn,
  };
}

/**
 * List directory structure under users/{userId}/ with folders and files.
 * Uses S3 delimiter to get folder structure.
 */
export async function listDirectoryStructure(
  userId: string,
  prefix?: string,
): Promise<{
  folders: Array<{ name: string; path: string }>;
  files: Array<{
    key: string;
    name: string;
    size: number;
    last_modified: string | null;
    content_type: string;
    presigned_url: string;
  }>;
  prefix: string;
}> {
  if (!env.S3_BUCKET_NAME) {
    throw new Error("S3_BUCKET_NAME not configured");
  }

  const basePrefix = `users/${userId}/`;
  const fullPrefix = prefix
    ? `${basePrefix}${prefix}${prefix.endsWith("/") ? "" : "/"}`
    : basePrefix;

  const client = getS3Client();
  const folders: Array<{ name: string; path: string }> = [];
  const files: Array<{
    key: string;
    name: string;
    size: number;
    last_modified: string | null;
    content_type: string;
    presigned_url: string;
  }> = [];

  let continuationToken: string | undefined;
  do {
    const command = new ListObjectsV2Command({
      Bucket: env.S3_BUCKET_NAME,
      Prefix: fullPrefix,
      Delimiter: "/",
      ContinuationToken: continuationToken,
    });

    const response = await client.send(command);

    // Get folders (CommonPrefixes)
    if (response.CommonPrefixes) {
      for (const commonPrefix of response.CommonPrefixes) {
        if (commonPrefix.Prefix) {
          const folderPath = commonPrefix.Prefix;
          const folderName = folderPath
            .slice(fullPrefix.length)
            .replace(/\/$/, "");
          folders.push({
            name: folderName,
            path: folderPath,
          });
        }
      }
    }

    // Get files (Contents)
    if (response.Contents) {
      for (const obj of response.Contents) {
        if (!obj.Key) continue;
        const s3Key = obj.Key;

        // Skip directory markers
        if (s3Key.endsWith("/")) {
          continue;
        }

        // Generate presigned URL
        const presignedUrl = await getSignedUrl(
          client,
          new GetObjectCommand({
            Bucket: env.S3_BUCKET_NAME,
            Key: s3Key,
          }),
          { expiresIn: 3600 }, // 1 hour
        );

        // Extract file name
        const fileName = s3Key.slice(fullPrefix.length);

        files.push({
          key: s3Key,
          name: fileName,
          size: obj.Size ?? 0,
          last_modified: obj.LastModified?.toISOString() ?? null,
          content_type: getContentTypeFromKey(s3Key),
          presigned_url: presignedUrl,
        });
      }
    }

    continuationToken = response.NextContinuationToken;
  } while (continuationToken);

  return {
    folders,
    files,
    prefix: fullPrefix,
  };
}

/**
 * List all files recursively from S3 for a user (no delimiter, flat list).
 * This returns all files under users/{userId}/ regardless of folder structure.
 */
export async function listAllS3Files(userId: string): Promise<
  Array<{
    key: string;
    name: string;
    size: number;
    last_modified: string | null;
    content_type: string;
    presigned_url: string;
  }>
> {
  if (!env.S3_BUCKET_NAME) {
    throw new Error("S3_BUCKET_NAME not configured");
  }

  const prefix = `users/${userId}/`;
  const client = getS3Client();
  const allFiles: Array<{
    key: string;
    name: string;
    size: number;
    last_modified: string | null;
    content_type: string;
    presigned_url: string;
  }> = [];

  let continuationToken: string | undefined;
  do {
    const command = new ListObjectsV2Command({
      Bucket: env.S3_BUCKET_NAME,
      Prefix: prefix,
      // No delimiter - this lists all files recursively
      ContinuationToken: continuationToken,
    });

    const response = await client.send(command);

    if (response.Contents) {
      // Generate presigned URLs for all files in this batch
      const filesWithUrls = await Promise.all(
        response.Contents.map(async (obj) => {
          if (!obj.Key || obj.Key.endsWith("/")) {
            return null; // Skip directory markers
          }

          const presignedUrl = await getSignedUrl(
            client,
            new GetObjectCommand({
              Bucket: env.S3_BUCKET_NAME,
              Key: obj.Key,
            }),
            { expiresIn: 3600 }, // 1 hour
          );

          // Extract file name (everything after the prefix)
          const fileName = obj.Key.slice(prefix.length);

          return {
            key: obj.Key,
            name: fileName,
            size: obj.Size ?? 0,
            last_modified: obj.LastModified?.toISOString() ?? null,
            content_type: getContentTypeFromKey(obj.Key),
            presigned_url: presignedUrl,
          };
        }),
      );

      // Filter out nulls and add to allFiles
      for (const file of filesWithUrls) {
        if (file) {
          allFiles.push(file);
        }
      }
    }

    continuationToken = response.NextContinuationToken;
  } while (continuationToken);

  return allFiles;
}

/**
 * List files from a session-specific folder.
 * Example: sessionId="abc123", subfolder="final" -> lists users/{userId}/abc123/final/
 */
export async function listSessionFiles(
  userId: string,
  sessionId: string,
  subfolder?: string,
): Promise<
  Array<{
    key: string;
    name: string;
    size: number;
    last_modified: string | null;
    content_type: string;
    presigned_url: string;
  }>
> {
  if (!env.S3_BUCKET_NAME) {
    throw new Error("S3_BUCKET_NAME not configured");
  }

  // Build prefix: users/{userId}/{sessionId}/subfolder/
  const basePrefix = `users/${userId}/${sessionId}/`;
  const fullPrefix = subfolder
    ? `${basePrefix}${subfolder}${subfolder.endsWith("/") ? "" : "/"}`
    : basePrefix;

  const client = getS3Client();
  const files: Array<{
    key: string;
    name: string;
    size: number;
    last_modified: string | null;
    content_type: string;
    presigned_url: string;
  }> = [];

  let continuationToken: string | undefined;
  do {
    const command = new ListObjectsV2Command({
      Bucket: env.S3_BUCKET_NAME,
      Prefix: fullPrefix,
      ContinuationToken: continuationToken,
    });

    const response = await client.send(command);

    if (response.Contents) {
      for (const obj of response.Contents) {
        if (!obj.Key) continue;
        const s3Key = obj.Key;

        // Skip directory markers
        if (s3Key.endsWith("/")) {
          continue;
        }

        // Generate presigned URL
        const presignedUrl = await getSignedUrl(
          client,
          new GetObjectCommand({
            Bucket: env.S3_BUCKET_NAME,
            Key: s3Key,
          }),
          { expiresIn: 3600 }, // 1 hour
        );

        // Extract file name
        const fileName = s3Key.slice(fullPrefix.length);

        files.push({
          key: s3Key,
          name: fileName,
          size: obj.Size ?? 0,
          last_modified: obj.LastModified?.toISOString() ?? null,
          content_type: getContentTypeFromKey(s3Key),
          presigned_url: presignedUrl,
        });
      }
    }

    continuationToken = response.NextContinuationToken;
  } while (continuationToken);

  return files;
}

/**
 * Get all assets for a user from the database.
 * Queries videoAssets table filtered by userId via videoSessions join.
 */
export async function getUserAssets(userId: string): Promise<
  Array<{
    id: string;
    assetType: string;
    url: string | null;
    sessionId: string;
    metadata: unknown;
    createdAt: Date;
  }>
> {
  const assets = await db
    .select({
      id: videoAssets.id,
      assetType: videoAssets.assetType,
      url: videoAssets.url,
      sessionId: videoAssets.sessionId,
      metadata: videoAssets.metadata,
      createdAt: videoAssets.createdAt,
    })
    .from(videoAssets)
    .innerJoin(videoSessions, eq(videoAssets.sessionId, videoSessions.id))
    .where(eq(videoSessions.userId, userId));

  return assets;
}
