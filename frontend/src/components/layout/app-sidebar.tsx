"use client";

import {
  ChevronRight,
  FileText,
  FolderOpen,
  History,
  Plus,
  HardDrive,
  Scissors,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import * as React from "react";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { NavUser } from "./nav-user";

// Dummy history IDs - replace with real data later
const dummyHistoryIds = [
  { id: "1", label: "Session 1" },
  { id: "2", label: "Session 2" },
  { id: "3", label: "Session 3" },
];

const navItems = [
  {
    title: "Create",
    url: "/dashboard/create",
    icon: Plus,
  },
  {
    title: "Assets",
    url: "/dashboard/assets",
    icon: FolderOpen,
  },
  {
    title: "History",
    icon: History,
    isCollapsible: true,
  },
  {
    title: "Hardcode Create",
    url: "/dashboard/hardcode-create",
    icon: FileText,
  },
  {
    title: "Hardcode Assets",
    url: "/dashboard/hardcode-assets",
    icon: HardDrive,
  },
  {
    title: "Edit",
    url: "/dashboard/editing",
    icon: Scissors,
  },
];

type User = {
  name: string | null;
  email: string | null;
  image: string | null;
};

export function AppSidebar({
  user,
  ...props
}: React.ComponentProps<typeof Sidebar> & { user: User }) {
  const pathname = usePathname();

  return (
    <Sidebar
      style={{ "--sidebar-width": "12rem" } as React.CSSProperties}
      collapsible="none"
      className="border-r p-2 px-1"
      {...props}
    >
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild className="md:h-8 md:p-0">
              <Link href="/dashboard">
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-medium">Pipeline</span>
                  <span className="truncate text-xs">Video Generator</span>
                </div>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent className="px-1.5 md:px-0">
            <SidebarMenu>
              {navItems.map((item) => {
                if (item.isCollapsible) {
                  const isHistoryActive = pathname.startsWith(
                    "/dashboard/history/",
                  );
                  return (
                    <Collapsible
                      key={item.title}
                      asChild
                      defaultOpen={isHistoryActive}
                    >
                      <SidebarMenuItem>
                        <CollapsibleTrigger asChild>
                          <SidebarMenuButton
                            isActive={isHistoryActive}
                            className="px-2.5 md:px-2"
                          >
                            <item.icon />
                            <span>{item.title}</span>
                            <ChevronRight className="ml-auto size-4 transition-transform duration-200 data-[state=open]:rotate-90" />
                          </SidebarMenuButton>
                        </CollapsibleTrigger>
                        <CollapsibleContent>
                          <ul className="mt-1 ml-4 space-y-1">
                            {dummyHistoryIds.map((historyItem) => {
                              const isActive =
                                pathname ===
                                `/dashboard/history/${historyItem.id}`;
                              return (
                                <SidebarMenuSubItem key={historyItem.id}>
                                  <SidebarMenuSubButton
                                    asChild
                                    isActive={isActive}
                                  >
                                    <Link
                                      href={`/dashboard/history/${historyItem.id}`}
                                    >
                                      {historyItem.label}
                                    </Link>
                                  </SidebarMenuSubButton>
                                </SidebarMenuSubItem>
                              );
                            })}
                          </ul>
                        </CollapsibleContent>
                      </SidebarMenuItem>
                    </Collapsible>
                  );
                }

                if (!item.url) {
                  return null;
                }

                const isActive = item.url === pathname;
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive}
                      className="px-2.5 md:px-2"
                    >
                      <Link href={item.url}>
                        <item.icon />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={user} />
      </SidebarFooter>
    </Sidebar>
  );
}
