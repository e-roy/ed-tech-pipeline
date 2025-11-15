import { redirect } from "next/navigation";
import { auth } from "@/server/auth";
import { AuthForm } from "@/components/login/auth-form";

// Ensure this route runs in Node.js runtime (not edge) for database access
export const runtime = "nodejs";

type SearchParams = Promise<{
  error?: string;
  success?: string;
  mode?: string;
}>;

export default async function LoginPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const session = await auth();
  const params = await searchParams;
  const error = params?.error;
  const success = params?.success;
  const mode = params?.mode === "signup" ? "signup" : "login";

  // Redirect if already logged in (middleware also handles this, but good to have here too)
  if (session) {
    redirect("/dashboard");
  }

  return (
    <div className="bg-background flex min-h-screen items-center justify-center">
      <div className="flex flex-1 flex-col justify-center px-4 py-10 lg:px-6">
        <AuthForm error={error} success={success} defaultTab={mode} />
      </div>
    </div>
  );
}
