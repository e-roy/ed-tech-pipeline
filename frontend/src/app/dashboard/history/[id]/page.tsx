"use client";

import { api } from "@/trpc/react";
import { format } from "date-fns";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TRPCClientError } from "@trpc/client";
import { use } from "react";

type Props = {
  params: Promise<{ id: string }>;
};

type SessionData = {
  id: string;
  userId: string;
  status: string;
  topic: string | null;
  learningObjective: string | null;
  confirmedFacts: unknown;
  generatedScript: unknown;
  createdAt: Date | null;
  updatedAt: Date | null;
};

export default function HistoryDetailPage({ params }: Props) {
  const { id: sessionId } = use(params);
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
  const queryResult = api.script.getSession.useQuery(
    { sessionId },
    { enabled: !!sessionId },
  );

  const session = queryResult.data as SessionData | undefined;
  const isLoading = queryResult.isLoading;
  const error = queryResult.error as Error | null;

  if (isLoading) {
    return (
      <div className="flex h-full flex-col p-4">
        <div className="mb-4">
          <Skeleton className="mb-2 h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <div className="text-center">
          <p className="text-destructive mb-2 font-medium">
            Error loading session
          </p>
          <p className="text-muted-foreground text-sm">
            {error instanceof TRPCClientError
              ? error.message
              : "An unexpected error occurred"}
          </p>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <p className="text-muted-foreground">Session not found</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-y-auto p-4">
      <div className="mb-4">
        <h1 className="text-2xl font-semibold">
          {session.topic ?? "Untitled Session"}
        </h1>
        <p className="text-muted-foreground text-sm">Session Details</p>
      </div>

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Overview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-muted-foreground text-sm font-medium">
                Status
              </label>
              <div className="mt-1">
                <Badge variant="outline">{session.status}</Badge>
              </div>
            </div>

            {session.topic && (
              <div>
                <label className="text-muted-foreground text-sm font-medium">
                  Topic
                </label>
                <p className="mt-1">{session.topic}</p>
              </div>
            )}

            {session.learningObjective && (
              <div>
                <label className="text-muted-foreground text-sm font-medium">
                  Learning Objective
                </label>
                <p className="mt-1">{session.learningObjective}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              {session.createdAt && (
                <div>
                  <label className="text-muted-foreground text-sm font-medium">
                    Created
                  </label>
                  <p className="mt-1 text-sm">
                    {format(
                      session.createdAt instanceof Date
                        ? session.createdAt
                        : new Date(session.createdAt),
                      "PPp",
                    )}
                  </p>
                </div>
              )}

              {session.updatedAt && (
                <div>
                  <label className="text-muted-foreground text-sm font-medium">
                    Updated
                  </label>
                  <p className="mt-1 text-sm">
                    {format(
                      session.updatedAt instanceof Date
                        ? session.updatedAt
                        : new Date(session.updatedAt),
                      "PPp",
                    )}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {session.confirmedFacts != null && (
          <Card>
            <CardHeader>
              <CardTitle>Confirmed Facts</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="bg-muted overflow-auto rounded-lg p-4 text-sm">
                {String(JSON.stringify(session.confirmedFacts, null, 2))}
              </pre>
            </CardContent>
          </Card>
        )}

        {session.generatedScript != null && (
          <Card>
            <CardHeader>
              <CardTitle>Generated Script</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="bg-muted overflow-auto rounded-lg p-4 text-sm">
                {String(JSON.stringify(session.generatedScript, null, 2))}
              </pre>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
