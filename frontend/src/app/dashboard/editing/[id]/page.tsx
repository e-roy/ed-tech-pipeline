import { auth } from "@/server/auth";
import { EditingPageClient } from "./editing-page-client";

type Props = {
  params: Promise<{ id: string }>;
};

export default async function EditingPage({ params }: Props) {
  const { id } = await params;
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
    <div className="flex h-full min-h-0 flex-col overflow-hidden p-4">
      <div className="mb-4 shrink-0">
        <h1 className="text-2xl font-semibold text-foreground">Video Editor</h1>
        <p className="text-muted-foreground text-sm">
          Preview and download your generated video
        </p>
      </div>
      <div className="flex-1 min-h-0 overflow-hidden">
        <EditingPageClient sessionId={id} userEmail={userEmail} />
      </div>
    </div>
  );
}
