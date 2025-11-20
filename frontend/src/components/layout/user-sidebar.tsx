import { auth } from "@/server/auth";
import { AppSidebar } from "./app-sidebar";

export async function UserSidebar() {
  const session = await auth();
  
  const user = session?.user
    ? {
        name: session.user.name ?? null,
        email: session.user.email ?? null,
        image: session.user.image ?? null,
      }
    : {
        name: null,
        email: null,
        image: null,
      };

  return <AppSidebar user={user} />;
}

