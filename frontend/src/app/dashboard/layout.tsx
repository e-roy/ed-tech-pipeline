import { SidebarProvider } from "@/components/ui/sidebar";
import { ChatProvider } from "@/components/layout/chat-context";
import { UserSidebar } from "@/components/layout/user-sidebar";
import { ThemeProvider } from "@/components/layout/theme-provider";
import { BackendTokenProvider } from "@/components/auth/backend-token-provider";
import { DashboardLayoutClient } from "./layout-client";
import { getBackendToken } from "@/lib/auth-token";

export default async function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  // Exchange NextAuth session for backend JWT token
  const backendToken = await getBackendToken();

  return (
    <ThemeProvider>
      <BackendTokenProvider token={backendToken}>
        <SidebarProvider>
          <ChatProvider>
            <div className="flex h-screen w-full">
              <UserSidebar />
              <DashboardLayoutClient>{children}</DashboardLayoutClient>
            </div>
          </ChatProvider>
        </SidebarProvider>
      </BackendTokenProvider>
    </ThemeProvider>
  );
}
