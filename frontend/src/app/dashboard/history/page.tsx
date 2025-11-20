"use client";

import { api } from "@/trpc/react";
import { useRouter } from "next/navigation";
import { formatDistanceToNow } from "date-fns";
import { useState } from "react";
import { toast } from "sonner";
import { Trash2, ArrowRight } from "lucide-react";
import {
  Empty,
  EmptyHeader,
  EmptyTitle,
  EmptyDescription,
} from "@/components/ui/empty";
import { Skeleton } from "@/components/ui/skeleton";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export default function HistoryPage() {
  const { data: sessions, isLoading } = api.script.list.useQuery();
  const utils = api.useUtils();

  const deleteMutation = (
    api.script as typeof api.script & {
      delete: typeof api.script.generate;
    }
  ).delete.useMutation({
    onSuccess: () => {
      toast.success("Session deleted successfully");
      void utils.script.list.invalidate();
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to delete session",
      );
    },
  });

  if (isLoading) {
    return (
      <div className="flex h-full flex-col p-4">
        <div className="mb-4">
          <Skeleton className="mb-2 h-8 w-48" />
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
              You haven&apos;t created any sessions yet.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <div className="space-y-3">
          {sessions.map((session) => (
            <SessionCard
              key={session.id}
              session={session}
              onDelete={() => {
                deleteMutation.mutate({ sessionId: session.id });
              }}
              isDeleting={deleteMutation.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface SessionCardProps {
  session: {
    id: string;
    topic: string | null;
    createdAt: Date | null;
  };
  onDelete: () => void;
  isDeleting: boolean;
}

function SessionCard({ session, onDelete, isDeleting }: SessionCardProps) {
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const router = useRouter();

  const handleDelete = async () => {
    onDelete();
    setIsDeleteDialogOpen(false);
  };

  const handleNavigate = () => {
    router.push(`/dashboard/history/${session.id}`);
  };

  const sessionTitle = session.topic ?? "Untitled";

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0 flex-1">
          <h3 className="truncate font-medium">{sessionTitle}</h3>
          {session.createdAt && (
            <p className="text-muted-foreground mt-1 text-sm">
              {formatDistanceToNow(new Date(session.createdAt), {
                addSuffix: true,
              })}
            </p>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleNavigate}
            className="flex items-center gap-2"
          >
            <span>View</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
          <AlertDialog
            open={isDeleteDialogOpen}
            onOpenChange={setIsDeleteDialogOpen}
          >
            <AlertDialogTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                disabled={isDeleting}
                className="shrink-0"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Session</AlertDialogTitle>
                <AlertDialogDescription>
                  {`Are you sure you want to delete "${sessionTitle}"? This action cannot be undone.`}
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                >
                  {isDeleting ? "Deleting..." : "Delete"}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
    </Card>
  );
}
