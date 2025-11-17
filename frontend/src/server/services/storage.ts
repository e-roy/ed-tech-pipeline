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
    // For output folder, list both traditional output and session image folders
    const prefixes: string[] = [];
    
    // Add traditional output prefix
    if (asset_type) {
      prefixes.push(`users/${userId}/output/${asset_type}/`);
    } else {
      prefixes.push(`users/${userId}/output/`);
    }
    
    // Also search for session image folders: users/{userId}/*/images/**
    // List all session folders under user prefix
    const userPrefix = `users/${userId}/`;
    const sessionFolders: string[] = [];
    
    // List all session folders (users/{userId}/{session_id}/)
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
            // Check if this session folder has an images subfolder
            // We'll list it directly: users/{userId}/{session_id}/images/
            const sessionIdMatch = prefix.Prefix.match(/^users\/\d+\/([^/]+)\/$/);
            if (sessionIdMatch) {
              sessionFolders.push(`${prefix.Prefix}images/`);
            }
          }
        }
      }
      
      continuationToken = response.NextContinuationToken;
    } while (continuationToken);
    
    // Now list files from each session's images folder
    for (const sessionImagesPrefix of sessionFolders) {
      let sessionContinuationToken: string | undefined;
      do {
        const command = new ListObjectsV2Command({
          Bucket: env.S3_BUCKET_NAME,
          Prefix: sessionImagesPrefix,
          MaxKeys: 1000,
          ContinuationToken: sessionContinuationToken,
        });

        const response = await client.send(command);
        if (response.Contents) {
        const validObjects = response.Contents.filter(
          (obj): obj is typeof obj & { Key: string } => !!obj.Key,
        )
            .filter((obj) => {
              // Only include image files, exclude segments.md, status.json, and diagram.png
              const key = obj.Key;
              const isImage = /\.(png|jpg|jpeg|gif|webp)$/i.test(key);
              return isImage && !key.endsWith("segments.md") && !key.endsWith("status.json") && !key.endsWith("diagram.png");
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
    
    // Also list traditional output folder files
    for (const prefix of prefixes) {
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
        content_type: obj.ContentType ?? "application/octet-stream",
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
