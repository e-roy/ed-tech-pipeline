"use client";

import { api } from "@/trpc/react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import {
  Empty,
  EmptyHeader,
  EmptyTitle,
  EmptyDescription,
} from "@/components/ui/empty";
import { Skeleton } from "@/components/ui/skeleton";
import { Card } from "@/components/ui/card";

export default function HistoryPage() {
  const { data: sessions, isLoading } = api.script.list.useQuery();

  if (isLoading) {
    return (
      <div className="flex h-full flex-col p-4">
        <div className="mb-4">
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col p-4">
      <div className="mb-4">
        <h1 className="text-2xl font-semibold">History</h1>
        <p className="text-muted-foreground text-sm">
          {sessions?.length ?? 0} session{sessions?.length !== 1 ? "s" : ""}
        </p>
      </div>

      {!sessions || sessions.length === 0 ? (
        <Empty>
          <EmptyHeader>
            <EmptyTitle>No sessions found</EmptyTitle>
            <EmptyDescription>
              You haven't created any sessions yet.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <div className="space-y-3">
          {sessions.map((session) => (
            <Link
              key={session.id}
              href={`/dashboard/history/${session.id}`}
              className="block"
            >
              <Card className="p-4 hover:bg-accent transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium truncate">
                      {session.topic || "Untitled"}
                    </h3>
                    {session.createdAt && (
                      <p className="text-sm text-muted-foreground mt-1">
                        {formatDistanceToNow(new Date(session.createdAt), {
                          addSuffix: true,
                        })}
                      </p>
                    )}
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

