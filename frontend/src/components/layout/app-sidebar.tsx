"use client";

import {
  ChevronRight,
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
  useSidebar,
} from "@/components/ui/sidebar";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { NavUser } from "./nav-user";
import { api } from "@/trpc/react";
import { Separator } from "@/components/ui/separator";

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
    title: "Edit",
    url: "/dashboard/editing/test",
    icon: Scissors,
  },
];

const navItemsSub = [
  {
    title: "Old Create Page",
    url: "/dashboard/old-create",
    icon: Plus,
  },
  {
    title: "Hardcode Assets",
    url: "/dashboard/hardcode-assets",
    icon: HardDrive,
  },
];

type User = {
  name: string | null;
  email: string | null;
  image: string | null;
};

type SessionListItem = {
  id: string;
  topic: string | null;
  createdAt: Date | null;
};

export function AppSidebar({
  user,
  ...props
}: React.ComponentProps<typeof Sidebar> & { user: User }) {
  const pathname = usePathname();
  const { mounted } = useSidebar();
  const queryResult = api.script.list.useQuery(undefined, {
    refetchOnWindowFocus: false,
  });

  const sessions = queryResult.data as SessionListItem[] | undefined;

  // Limit to 20 most recent sessions for sidebar
  const recentSessions = React.useMemo(() => {
    if (!sessions || !Array.isArray(sessions)) return [];
    return sessions.slice(0, 20);
  }, [sessions]);

  // Compute if we're on a history route (same on server and client)
  const isOnHistoryRoute =
    pathname.startsWith("/dashboard/history/") ||
    pathname === "/dashboard/history";

  // Only show active styling after mount to avoid hydration mismatch
  const isHistoryActive = mounted && isOnHistoryRoute;

  return (
    <Sidebar
      style={{ "--sidebar-width": "16rem" } as React.CSSProperties}
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
                  return (
                    <Collapsible
                      key={item.title}
                      id="sidebar-history-collapsible"
                      asChild
                      defaultOpen={isOnHistoryRoute}
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
                            {recentSessions.length === 0 ? (
                              <li className="text-muted-foreground px-2 py-1 text-xs">
                                No sessions
                              </li>
                            ) : (
                              recentSessions.map((session) => {
                                const isActive =
                                  pathname ===
                                  `/dashboard/history/${session.id}`;
                                const topic = session.topic ?? "Untitled";
                                return (
                                  <SidebarMenuSubItem key={session.id}>
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <SidebarMenuSubButton
                                          asChild
                                          isActive={isActive}
                                          className="min-w-0"
                                        >
                                          <Link
                                            href={`/dashboard/history/${session.id}`}
                                            className="block truncate"
                                          >
                                            {topic}
                                          </Link>
                                        </SidebarMenuSubButton>
                                      </TooltipTrigger>
                                      <TooltipContent>
                                        <p>{topic}</p>
                                      </TooltipContent>
                                    </Tooltip>
                                  </SidebarMenuSubItem>
                                );
                              })
                            )}
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
        <Separator />
        <SidebarGroup>
          <SidebarGroupContent className="px-1.5 md:px-0">
            <SidebarMenu>
              {navItemsSub.map((item) => {
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
