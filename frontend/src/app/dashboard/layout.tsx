import { SidebarProvider } from "@/components/ui/sidebar";
import { FactExtractionProvider } from "@/components/fact-extraction/FactExtractionContext";
import { UserSidebar } from "@/components/layout/user-sidebar";
import { ThemeProvider } from "@/components/layout/theme-provider";
import { DashboardLayoutClient } from "./layout-client";
import { auth } from "@/server/auth";
import { logUserDetails } from "@/lib/logger";

export default async function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const session = await auth();
  logUserDetails(session);

  return (
    <ThemeProvider>
      <SidebarProvider>
        <FactExtractionProvider>
          <div className="flex h-screen w-full">
            <UserSidebar />
            <DashboardLayoutClient>{children}</DashboardLayoutClient>
          </div>
        </FactExtractionProvider>
      </SidebarProvider>
    </ThemeProvider>
  );
}
