import { SidebarProvider } from "@/components/ui/sidebar";
import { ChatProvider } from "@/components/layout/chat-context";
import { UserSidebar } from "@/components/layout/user-sidebar";
import { ThemeProvider } from "@/components/layout/theme-provider";
import { DashboardLayoutClient } from "./layout-client";

export default async function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  // Get user info from NextAuth session

  return (
    <ThemeProvider>
      <SidebarProvider>
        <ChatProvider>
          <div className="flex h-screen w-full">
            <UserSidebar />
            <DashboardLayoutClient>{children}</DashboardLayoutClient>
          </div>
        </ChatProvider>
      </SidebarProvider>
    </ThemeProvider>
  );
}
