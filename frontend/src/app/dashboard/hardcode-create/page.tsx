import { auth } from "@/server/auth";
import { HardcodeCreateForm } from "./hardcode-create-form";

export default async function HardcodeCreatePage() {
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
        <h1 className="text-2xl font-semibold">Hardcode Create</h1>
        <p className="text-muted-foreground text-sm">
          Manually create story segments and generate images
        </p>
      </div>
      <HardcodeCreateForm userEmail={userEmail} />
    </div>
  );
}

