"use client";

import { usePathname } from "next/navigation";
import { SidebarInset } from "@/components/ui/sidebar";
import { ChatPreview } from "@/components/chat/chat-preview";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";

export function DashboardLayoutClient({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname();

  // Show double-sided panel for create and history routes
  const showDoublePanel = pathname === "/dashboard/create";

  return (
    <SidebarInset className="flex-1">
      {showDoublePanel ? (
        <ResizablePanelGroup direction="horizontal" className="h-full">
          <ResizablePanel defaultSize={20} minSize={20}>
            <ChatPreview />
          </ResizablePanel>
          <ResizableHandle />
          <ResizablePanel defaultSize={80} minSize={70} className="p-2">
            <div className="flex h-full flex-col rounded-xl border">
              {children}
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      ) : (
        <div className="h-full overflow-hidden">
          <div className="flex h-full flex-col">{children}</div>
        </div>
      )}
    </SidebarInset>
  );
}
