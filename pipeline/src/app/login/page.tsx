import { redirect } from "next/navigation";
import { auth, signIn } from "@/server/auth";
import { env } from "@/env";
// import { Button } from "@/components/ui/button";

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ callbackUrl?: string; error?: string }>;
}) {
  const session = await auth();
  const params = await searchParams;

  // If already signed in, redirect to callback URL or app dashboard
  if (session) {
    redirect(params.callbackUrl ?? "/app");
  }

  // Check if Google OAuth is configured
  const googleConfigured = !!env.AUTH_GOOGLE_ID && !!env.AUTH_GOOGLE_SECRET;

  return (
    <div className="flex min-h-screen flex-col items-center justify-center">
      <div className="container flex flex-col items-center gap-8 px-4">
        <div className="flex flex-col items-center gap-2 text-center">
          <h1 className="text-4xl font-bold">Sign In / Sign Up</h1>
          {!googleConfigured ? (
            <div className="max-w-md rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-4">
              <p className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                Google OAuth not configured
              </p>
              <p className="mt-2 text-xs text-yellow-600 dark:text-yellow-500">
                To enable Google authentication, add AUTH_GOOGLE_ID and
                AUTH_GOOGLE_SECRET to your .env.local file. Get these from the
                Google Cloud Console.
              </p>
            </div>
          ) : (
            <p className="text-muted-foreground max-w-md">
              Sign in with your Google account to continue. New users will
              automatically have an account created.
            </p>
          )}
        </div>
        <form
          action={async () => {
            "use server";
            await signIn("google", {
              redirectTo: params.callbackUrl ?? "/app",
            });
          }}
          className="flex w-full max-w-md flex-col gap-4"
        >
          {params.error && (
            <p className="text-destructive text-sm">
              {params.error === "Configuration"
                ? "Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your environment variables."
                : "An error occurred during sign in."}
            </p>
          )}
          <button type="submit" className="w-full" disabled={!googleConfigured}>
            {googleConfigured ? (
              <>
                <svg
                  className="mr-2 h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    fill="#4285F4"
                  />
                  <path
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    fill="#34A853"
                  />
                  <path
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    fill="#FBBC05"
                  />
                  <path
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    fill="#EA4335"
                  />
                </svg>
                Sign in with Google
              </>
            ) : (
              "Google OAuth Not Configured"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
