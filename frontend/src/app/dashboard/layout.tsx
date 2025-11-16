import { SidebarProvider } from "@/components/ui/sidebar";
import { ChatProvider } from "@/components/layout/chat-context";
import { UserSidebar } from "@/components/layout/user-sidebar";
import { ThemeProvider } from "@/components/layout/theme-provider";
import { UserProvider } from "@/components/auth/user-provider";
import { DashboardLayoutClient } from "./layout-client";
import { auth } from "@/server/auth";

export default async function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  // Get user info from NextAuth session
  const session = await auth();
  const userId = session?.user?.id;
  const userEmail = session?.user?.email;

  return (
    <ThemeProvider>
      <UserProvider userId={userId} userEmail={userEmail}>
        <SidebarProvider>
          <ChatProvider>
            <div className="flex h-screen w-full">
              <UserSidebar />
              <DashboardLayoutClient>{children}</DashboardLayoutClient>
            </div>
          </ChatProvider>
        </SidebarProvider>
      </UserProvider>
    </ThemeProvider>
  );
}
