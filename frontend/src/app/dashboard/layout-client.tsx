"use client";

import { SidebarInset } from "@/components/ui/sidebar";

export function DashboardLayoutClient({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <SidebarInset className="flex-1">
      <div className="h-full overflow-hidden">
        <div className="flex h-full flex-col">{children}</div>
      </div>
    </SidebarInset>
  );
}
