import { SidebarProvider } from "@/components/ui/sidebar";
import { ChatProvider } from "@/components/chat/chat-context";
import { FactExtractionProvider } from "@/components/fact-extraction/FactExtractionContext";
import { UserSidebar } from "@/components/layout/user-sidebar";
import { ThemeProvider } from "@/components/layout/theme-provider";
import { DashboardLayoutClient } from "./layout-client";

export default async function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <ThemeProvider>
      <SidebarProvider>
        <ChatProvider>
          <FactExtractionProvider>
            <div className="flex h-screen w-full">
              <UserSidebar />
              <DashboardLayoutClient>{children}</DashboardLayoutClient>
            </div>
          </FactExtractionProvider>
        </ChatProvider>
      </SidebarProvider>
    </ThemeProvider>
  );
}
