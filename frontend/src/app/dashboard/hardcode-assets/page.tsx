import { auth } from "@/server/auth";
import { HardcodeAssetsView } from "@/components/hardcode-assets/hardcode-assets-view";
import {
  getUserAssets,
  listDirectoryStructure,
  listAllS3Files,
} from "@/server/services/storage";
import { Card } from "@/components/ui/card";

export default async function HardcodeAssetsPage() {
  const session = await auth();
  const userId = session?.user?.id;
  const userEmail = session?.user?.email ?? null;

  if (!userId || !userEmail) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-6">
        <p className="text-muted-foreground">Please log in to continue.</p>
      </div>
    );
  }

  try {
    // Fetch user assets from database
    const userAssets = await getUserAssets(userId);

    // Fetch root S3 directory structure
    const s3RootData = await listDirectoryStructure(userId, "");

    // Fetch all S3 files (flat list)
    const allS3Files = await listAllS3Files(userId);

    return (
      <div className="flex h-full flex-col p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold">Hardcode Assets</h1>
          <p className="text-muted-foreground text-sm">
            Browse and download files from your S3 storage
          </p>
        </div>
        <HardcodeAssetsView
          userAssets={userAssets}
          s3RootData={s3RootData}
          allS3Files={allS3Files}
          userId={userId}
          userEmail={userEmail}
        />
      </div>
    );
  } catch (error) {
    console.error("Failed to load assets:", error);
    return (
      <div className="flex h-full flex-col items-center justify-center p-6">
        <Card className="p-6">
          <p className="text-destructive">
            Error loading assets:{" "}
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </Card>
      </div>
    );
  }
}
