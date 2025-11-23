"use client";

import { Plus, Settings, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface ChatHeaderProps {
  sessionId: string | null;
  copied: boolean;
  onNewChat: () => void;
  onClearSession: () => void;
  onDeleteSession: () => void;
  onCopySessionId: () => void;
}

export function ChatHeader({
  sessionId,
  copied,
  onNewChat,
  onClearSession,
  onDeleteSession,
  onCopySessionId,
}: ChatHeaderProps) {
  return (
    <div className="flex h-15 shrink-0 items-center justify-between gap-2 border-b px-4 py-3">
      <div className="flex items-center gap-2">
        <h2 className="text-sm font-semibold">Chat</h2>
      </div>
      <div className="flex items-center gap-4">
        {sessionId && (
          <Button
            variant="outline"
            size="sm"
            onClick={onNewChat}
            title="Create new chat"
          >
            <Plus className="h-4 w-4" /> New Chat
          </Button>
        )}
        {sessionId && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                title="Session settings"
              >
                <Settings className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-80">
              <DropdownMenuItem
                onClick={onCopySessionId}
                className="cursor-pointer font-mono text-xs"
              >
                <div className="flex w-full items-center justify-between gap-2">
                  <span className="text-muted-foreground truncate">
                    {sessionId}
                  </span>
                  {copied ? (
                    <Check className="h-4 w-4 shrink-0 text-green-600" />
                  ) : (
                    <Copy className="h-4 w-4 shrink-0" />
                  )}
                </div>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={onClearSession}
                className="cursor-pointer"
              >
                Clear Session
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={onDeleteSession}
                className="cursor-pointer text-red-600 focus:text-red-600"
              >
                Delete Session
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </div>
  );
}

