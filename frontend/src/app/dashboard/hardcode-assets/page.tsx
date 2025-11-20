import { auth } from "@/server/auth";
import { HardcodeAssetsView } from "./hardcode-assets-view";

export default async function HardcodeAssetsPage() {
  const session = await auth();
  const userEmail = session?.user?.email ?? null;

  if (!userEmail) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-6">
        <p className="text-muted-foreground">Please log in to continue.</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Hardcode Assets</h1>
        <p className="text-muted-foreground text-sm">
          Browse and download files from your S3 storage
        </p>
      </div>
      <HardcodeAssetsView userEmail={userEmail} />
    </div>
  );
}

