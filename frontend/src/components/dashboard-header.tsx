import { auth, signOut } from "@/server/auth";
import { Button } from "@/components/ui/button";

export async function DashboardHeader() {
  const session = await auth();

  if (!session) {
    return null;
  }

  return (
    <header className="bg-background border-b">
      <div className="container flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold">Dashboard</h1>
        </div>
        <div className="flex items-center gap-4">
          {session.user?.name && (
            <span className="text-muted-foreground text-sm">
              {session.user.name}
            </span>
          )}
          {session.user?.email && !session.user?.name && (
            <span className="text-muted-foreground text-sm">
              {session.user.email}
            </span>
          )}
          <form
            action={async () => {
              "use server";
              await signOut({ redirectTo: "/login" });
            }}
          >
            <Button type="submit" variant="outline" size="sm">
              Sign Out
            </Button>
          </form>
        </div>
      </div>
    </header>
  );
}
