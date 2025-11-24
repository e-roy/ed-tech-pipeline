"use client";

import { api } from "@/trpc/react";
import { useRouter } from "next/navigation";
import { formatDistanceToNow } from "date-fns";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Trash2, ArrowRight, Loader2, X, Webhook } from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Progress } from "@/components/ui/progress";
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
  const router = useRouter();
  const [showDeleteAllDialog, setShowDeleteAllDialog] = useState(false);
  const [isDeletingAll, setIsDeletingAll] = useState(false);
  const [isTestingWebhook, setIsTestingWebhook] = useState(false);
  
  // Check for active processing
  const { data: processingStatus, refetch: refetchProcessing } = api.script.checkProcessing.useQuery(
    {},
    {
      refetchInterval: 5000, // Poll every 5 seconds
    }
  );
  
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [progressMessage, setProgressMessage] = useState<string>("");
  
  // Connect to WebSocket if there's an active session
  const { lastMessage, isConnected } = useWebSocket(activeSessionId);
  
  // Update active session when processing status changes
  useEffect(() => {
    if (processingStatus?.in_progress && processingStatus.session_id) {
      setActiveSessionId(processingStatus.session_id);
    } else {
      setActiveSessionId(null);
      setProgress(0);
      setProgressMessage("");
    }
  }, [processingStatus]);
  
  // Update progress from WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.progress) {
        const completed = lastMessage.progress.completed || 0;
        const total = lastMessage.progress.total || 1;
        setProgress(Math.round((completed / total) * 100));
        setProgressMessage(lastMessage.message || "");
      } else if (lastMessage.status) {
        setProgressMessage(lastMessage.message || lastMessage.status);
      }
    }
  }, [lastMessage]);
  
  const cancelMutation = api.script.cancelProcessing.useMutation({
    onSuccess: (result) => {
      toast.success(result.message);
      setActiveSessionId(null);
      setProgress(0);
      setProgressMessage("");
      void refetchProcessing();
      void utils.script.list.invalidate();
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to cancel processing",
      );
    },
  });
  
  const handleCancel = () => {
    cancelMutation.mutate({});
  };
  
  const testWebhookMutation = api.script.testWebhook.useMutation({
    onSuccess: (result) => {
      if (result.success) {
        toast.success(result.message);
      } else {
        toast.error(result.message || "Webhook test failed");
      }
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Failed to test webhook",
      );
    },
    onSettled: () => {
      setIsTestingWebhook(false);
    },
  });
  
  const handleTestWebhook = () => {
    setIsTestingWebhook(true);
    testWebhookMutation.mutate({});
  };

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

  // Handle bulk delete all
  const handleDeleteAll = async () => {
    if (!sessions || sessions.length === 0 || isDeletingAll) return;

    setIsDeletingAll(true);
    const sessionIds = sessions.map((s) => s.id);
    const failedDeletions: string[] = [];
    let deletedCount = 0;

    try {
      // Delete each session with 200ms delay
      for (let i = 0; i < sessionIds.length; i++) {
        const sessionId = sessionIds[i];
        if (!sessionId) continue; // Type guard for TypeScript
        try {
          await deleteMutation.mutateAsync({ sessionId });
          deletedCount++;

          // Wait 200ms before next deletion (except for the last one)
          if (i < sessionIds.length - 1) {
            await new Promise((resolve) => setTimeout(resolve, 200));
          }
        } catch (error) {
          failedDeletions.push(sessionId);
        }
      }

      // Refresh the list
      await utils.script.list.invalidate();

      // Show results
      if (failedDeletions.length === 0) {
        toast.success(`Successfully deleted ${deletedCount} session(s)`);
      } else {
        toast.error(
          `Deleted ${deletedCount} session(s). Failed to delete ${failedDeletions.length} session(s).`,
        );
      }

      // Navigate away if we're on a session page (sessions might be deleted)
      router.push("/dashboard/create");
    } catch (error) {
      toast.error("An error occurred during bulk deletion");
    } finally {
      setIsDeletingAll(false);
      setShowDeleteAllDialog(false);
    }
  };

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
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">History</h1>
          <p className="text-muted-foreground text-sm">
            {sessions?.length ?? 0} session{sessions?.length !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handleTestWebhook}
            disabled={isTestingWebhook}
          >
            <Webhook className="mr-2 h-4 w-4" />
            {isTestingWebhook ? "Testing..." : "Test Webhook"}
          </Button>
          {sessions && sessions.length > 0 && (
            <Button
              variant="destructive"
              onClick={() => setShowDeleteAllDialog(true)}
              disabled={isDeletingAll}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete All
            </Button>
          )}
        </div>
      </div>
      
      {/* Progress Bar - Only show when processing */}
      {processingStatus?.in_progress && activeSessionId && (
        <Card className="mb-4 p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm font-medium">Processing video...</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCancel}
              disabled={cancelMutation.isPending}
            >
              <X className="mr-2 h-4 w-4" />
              Cancel
            </Button>
          </div>
          <Progress value={progress} className="mb-2" />
          {progressMessage && (
            <p className="text-muted-foreground text-xs">{progressMessage}</p>
          )}
          {!isConnected && (
            <p className="text-muted-foreground text-xs mt-1">
              Connecting to progress updates...
            </p>
          )}
        </Card>
      )}

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
        <div className="space-y-3 overflow-y-auto">
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

      {/* Delete All Confirmation Dialog */}
      <AlertDialog
        open={showDeleteAllDialog}
        onOpenChange={(open) => {
          // Prevent closing during deletion
          if (!isDeletingAll && !open) {
            setShowDeleteAllDialog(false);
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {isDeletingAll
                ? "Deleting All Sessions..."
                : "Delete All Sessions"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {isDeletingAll ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="size-4 animate-spin" />
                  <span>
                    Please wait while all sessions are being deleted...
                  </span>
                </div>
              ) : (
                <>
                  Are you sure you want to delete all {sessions?.length ?? 0}{" "}
                  session
                  {sessions && sessions.length !== 1 ? "s" : ""}? This action
                  cannot be undone.
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() => setShowDeleteAllDialog(false)}
              disabled={isDeletingAll}
            >
              Cancel
            </AlertDialogCancel>
            {!isDeletingAll && (
              <Button
                onClick={handleDeleteAll}
                variant="destructive"
                type="button"
              >
                Delete All
              </Button>
            )}
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
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
    router.push(`/dashboard/create?sessionId=${session.id}`);
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
                <Button
                  onClick={handleDelete}
                  disabled={isDeleting}
                  variant="destructive"
                  type="button"
                >
                  {isDeleting ? "Deleting..." : "Delete"}
                </Button>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
    </Card>
  );
}
