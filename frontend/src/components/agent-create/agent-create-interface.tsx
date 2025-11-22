"use client";

import type { FileUIPart } from "ai";
import {
  Conversation,
  ConversationContent,
} from "@/components/ai-elements/conversation";
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputAttachments,
  PromptInputAttachment,
  PromptInputActionMenu,
  PromptInputActionMenuTrigger,
  PromptInputActionMenuContent,
  PromptInputActionAddAttachments,
} from "@/components/ai-elements/prompt-input";
import {
  Message,
  MessageContent,
  MessageResponse,
  MessageAttachments,
  MessageAttachment,
} from "@/components/ai-elements/message";
import { DocumentEditor } from "@/components/agent-create/document-editor";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import { useAgentCreateStore } from "@/stores/agent-create-store";
import { ScriptGenerationChainOfThought } from "@/components/generation/ScriptGenerationChainOfThought";
import { useEffect, useState } from "react";
import { Plus, Paperclip, Settings, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Suggestions, Suggestion } from "@/components/ai-elements/suggestion";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { api } from "@/trpc/react";
import { useRouter, usePathname } from "next/navigation";
import { toast } from "sonner";

type AgentCreateInterfaceProps = {
  /**
   * Optional sessionId to load on mount.
   * If provided, the component will load the session data.
   */
  sessionId?: string | null;
  /**
   * Whether to show the "New Chat" button in the header.
   * @default true
   */
  showNewChatButton?: boolean;
};

export function AgentCreateInterface({
  sessionId: externalSessionId,
  showNewChatButton = true,
}: AgentCreateInterfaceProps) {
  const {
    messages,
    isLoading,
    error,
    workflowStep,
    thinkingStatus,
    handleSubmit,
    sessionId: storeSessionId,
    reset,
    setSessionId,
    loadSession,
    facts,
    selectedFacts,
    narration,
    childAge,
    childInterest,
    showFactSelectionPrompt,
    showNarrationReviewPrompt,
    handleSubmitFacts,
    setIsVideoGenerating,
  } = useAgentCreateStore();

  // Video generation state
  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [videoSuccess, setVideoSuccess] = useState(false);

  // Delete session dialog state
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [copied, setCopied] = useState(false);

  // Router and utils for navigation and cache invalidation
  const router = useRouter();
  const pathname = usePathname();
  const utils = api.useUtils();

  // tRPC mutation for video approval
  const approveMutation = api.script.approve.useMutation({
    onSuccess: () => {
      setIsGeneratingVideo(false);
      setVideoSuccess(true);
      setVideoError(null);
      setIsVideoGenerating(true); // Enable WebSocket connection

      // Add success message to chat
      const successMessage = {
        role: "assistant" as const,
        content:
          "🎉 Video generation started! Your video is being created and will be ready soon. You can check the status in your dashboard.",
        id: Date.now().toString(),
      };
      const store = useAgentCreateStore.getState();
      store.addMessage(successMessage);
    },
    onError: (error) => {
      setIsGeneratingVideo(false);
      setVideoError(error.message);
      setIsVideoGenerating(false); // Disable WebSocket connection

      // Add error message to chat
      const errorMessage = {
        role: "assistant" as const,
        content: `❌ Failed to start video generation: ${error.message}. Please try again.`,
        id: Date.now().toString(),
      };
      const store = useAgentCreateStore.getState();
      store.addMessage(errorMessage);
    },
  });

  // tRPC mutation for deleting session
  const deleteMutation = api.script.delete.useMutation({
    onSuccess: () => {
      toast.success("Session deleted successfully");

      // Invalidate history list to refresh
      void utils.script.list.invalidate();

      // Reset local state
      reset();
      setSessionId(null);

      // Navigate away if we're on the session detail page
      if (pathname?.includes("/history/")) {
        router.push("/dashboard/create");
      }
    },
    onError: (error) => {
      toast.error(`Failed to delete session: ${error.message}`);

      // Add error message to chat
      const errorMessage = {
        role: "assistant" as const,
        content: `Failed to delete session: ${error.message}`,
        id: Date.now().toString(),
      };
      const store = useAgentCreateStore.getState();
      store.addMessage(errorMessage);
    },
  });

  // Handler for clearing session (local only)
  const handleClearSession = () => {
    reset();
    setSessionId(null);
  };

  // Handler for copying session ID to clipboard
  const handleCopySessionId = async () => {
    if (displaySessionId) {
      try {
        await navigator.clipboard.writeText(displaySessionId);
        setCopied(true);
        toast.success("Session ID copied to clipboard");
        setTimeout(() => setCopied(false), 2000);
      } catch {
        toast.error("Failed to copy session ID");
      }
    }
  };

  // Handler for deleting session (from DB)
  const handleDeleteSession = () => {
    if (storeSessionId) {
      deleteMutation.mutate({ sessionId: storeSessionId });
    }
    setShowDeleteDialog(false);
  };

  // Handler for video creation
  const handleSubmitVideo = async () => {
    if (!narration || !selectedFacts || !storeSessionId) {
      setVideoError("Missing required data for video generation");
      return;
    }

    setIsGeneratingVideo(true);
    setVideoError(null);
    setVideoSuccess(false);

    // Calculate cost and duration from narration
    const cost = 0; // You may want to calculate this based on your pricing
    const duration = narration.total_duration || 60;

    // Add user message confirming video generation
    const confirmMessage = {
      role: "user" as const,
      content: "Start generating the video",
      id: Date.now().toString(),
    };
    const store = useAgentCreateStore.getState();
    store.addMessage(confirmMessage);

    // Prepare facts for the API
    const factsForApi = selectedFacts.map((f) => ({
      concept: f.concept,
      details: f.details,
    }));

    try {
      await approveMutation.mutateAsync({
        script: narration,
        topic: factsForApi[0]?.concept ?? "Educational Content",
        facts: factsForApi,
        cost,
        duration,
        sessionId: storeSessionId,
      });
    } catch (error) {
      // Error is handled in onError callback
      console.error("Video generation error:", error);
    }
  };

  // Load session data on mount if externalSessionId is provided
  useEffect(() => {
    if (externalSessionId && externalSessionId !== storeSessionId) {
      setSessionId(externalSessionId);
      loadSession(externalSessionId).catch((err) => {
        console.error("Failed to load session:", err);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [externalSessionId]);

  const handleNewChat = () => {
    reset();
    setSessionId(null);
  };

  const displaySessionId = externalSessionId ?? storeSessionId;

  return (
    <div className="flex h-full w-full flex-col">
      <ResizablePanelGroup
        id="agent-create-panels"
        direction="horizontal"
        className="h-full min-h-0"
      >
        {/* Chat Panel */}
        <ResizablePanel defaultSize={40} minSize={30} className="flex flex-col">
          <div className="bg-background flex h-full min-h-0 flex-col border-r">
            <div className="flex shrink-0 items-center justify-between gap-2 border-b px-4 py-3">
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-semibold">Chat</h2>
                {showNewChatButton && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={handleNewChat}
                    title="Create new chat"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                )}
              </div>
              <div className="flex items-center gap-2">
                {displaySessionId && (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        title="Session settings"
                      >
                        <Settings className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-80">
                      <DropdownMenuItem
                        onClick={handleCopySessionId}
                        className="cursor-pointer font-mono text-xs"
                      >
                        <div className="flex w-full items-center justify-between gap-2">
                          <span className="text-muted-foreground truncate">
                            {displaySessionId}
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
                        onClick={handleClearSession}
                        className="cursor-pointer"
                      >
                        Clear Session
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => setShowDeleteDialog(true)}
                        className="cursor-pointer text-red-600 focus:text-red-600"
                      >
                        Delete Session
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                )}
              </div>
            </div>
            <Conversation className="min-h-0 flex-1">
              <ConversationContent className="flex min-h-full flex-col">
                {messages.length === 0 ? (
                  <div className="flex flex-1 flex-col items-center justify-center p-8">
                    <Message from="assistant">
                      <MessageContent>
                        <div className="space-y-4">
                          <div>
                            <h3 className="mb-2 text-lg font-semibold">
                              Create a Personalized Educational Video
                            </h3>
                            <p className="text-muted-foreground text-sm">
                              I&apos;ll help you create an engaging biology
                              video for your student. You can share lesson
                              materials to get started, or tell me about your
                              student&apos;s age and interests for
                              personalization.
                            </p>
                          </div>
                          <Suggestions>
                            <Suggestion
                              suggestion="Tell me about the student"
                              onClick={() => {
                                const textarea = document.querySelector(
                                  'textarea[placeholder*="Tell me about"]',
                                );
                                if (textarea instanceof HTMLTextAreaElement) {
                                  textarea.value =
                                    "My student is __ years old and loves ___";
                                  textarea.focus();
                                  // Move cursor to first blank
                                  textarea.setSelectionRange(14, 16);
                                }
                              }}
                            />
                            <Suggestion
                              suggestion="Upload lesson PDF"
                              onClick={() => {
                                const fileInput = document.querySelector(
                                  'input[type="file"][accept*="pdf"]',
                                );
                                if (fileInput instanceof HTMLInputElement) {
                                  fileInput.click();
                                }
                              }}
                            />
                            <Suggestion
                              suggestion="Paste lesson text"
                              onClick={() => {
                                const textarea = document.querySelector(
                                  'textarea[placeholder*="Tell me about"]',
                                );
                                if (textarea instanceof HTMLTextAreaElement) {
                                  textarea.focus();
                                }
                              }}
                            />
                          </Suggestions>
                        </div>
                      </MessageContent>
                    </Message>
                  </div>
                ) : (
                  <>
                    {messages.map((message, i) => {
                      // Extract display content (hide extracted PDF text)
                      let displayContent = message.content;
                      if (
                        message.role === "user" &&
                        displayContent.includes(
                          "--- Extracted Learning Materials",
                        )
                      ) {
                        const extractedIndex = displayContent.indexOf(
                          "--- Extracted Learning Materials",
                        );
                        if (extractedIndex > 0) {
                          displayContent = displayContent
                            .substring(0, extractedIndex)
                            .trim();
                        } else {
                          displayContent = "";
                        }
                      }

                      const files = (message.files ??
                        []) as unknown as FileUIPart[];
                      const hasFiles = files.length > 0;

                      return (
                        <Message key={message.id ?? i} from={message.role}>
                          {hasFiles && (
                            <MessageAttachments>
                              {files.map((file, fileIndex) => (
                                <MessageAttachment
                                  key={fileIndex}
                                  data={file}
                                />
                              ))}
                            </MessageAttachments>
                          )}
                          {displayContent && (
                            <MessageContent>
                              <MessageResponse>
                                {displayContent}
                              </MessageResponse>
                            </MessageContent>
                          )}
                          {!displayContent && hasFiles && (
                            <MessageContent>
                              <div className="text-muted-foreground text-sm">
                                PDF attached
                              </div>
                            </MessageContent>
                          )}
                        </Message>
                      );
                    })}
                    {showFactSelectionPrompt && facts.length > 0 && (
                      <Message from="assistant">
                        <MessageContent>
                          <div className="space-y-3">
                            <p>
                              I&apos;ve found {facts.length} key facts. Please
                              review them on the right and select the ones
                              you&apos;d like to focus on for the video.
                            </p>
                            {selectedFacts.length > 0 && (
                              <Alert className="bg-primary/10">
                                <AlertDescription>
                                  <div className="flex w-full items-center justify-between">
                                    <span className="text-sm font-medium">
                                      {selectedFacts.length} fact
                                      {selectedFacts.length !== 1
                                        ? "s"
                                        : ""}{" "}
                                      selected
                                    </span>
                                    <Button
                                      onClick={handleSubmitFacts}
                                      size="sm"
                                      disabled={isLoading}
                                    >
                                      Create Narration
                                    </Button>
                                  </div>
                                </AlertDescription>
                              </Alert>
                            )}
                          </div>
                        </MessageContent>
                      </Message>
                    )}
                    {showNarrationReviewPrompt && narration && (
                      <Message from="assistant">
                        <MessageContent>
                          <div className="space-y-3">
                            <p>
                              I&apos;ve created your narration script!
                              Here&apos;s a summary:
                            </p>
                            <div className="bg-muted rounded-lg p-3 text-sm">
                              <div className="flex flex-wrap gap-4">
                                <div>
                                  <span className="text-muted-foreground">
                                    Duration:
                                  </span>{" "}
                                  {narration.total_duration}s
                                </div>
                                <div>
                                  <span className="text-muted-foreground">
                                    Segments:
                                  </span>{" "}
                                  {narration.segments.length}
                                </div>
                                <div>
                                  <span className="text-muted-foreground">
                                    Reading Level:
                                  </span>{" "}
                                  {narration.reading_level}
                                </div>
                                <div>
                                  <span className="text-muted-foreground">
                                    Key Terms:
                                  </span>{" "}
                                  {narration.key_terms_count}
                                </div>
                              </div>
                            </div>
                            <p className="text-muted-foreground text-sm">
                              You can review and edit the script on the right.
                              When you&apos;re ready, you can proceed to
                              generate the video.
                            </p>

                            <Alert className="bg-primary/10">
                              <AlertDescription>
                                <div className="flex w-full items-center justify-between">
                                  <div className="flex flex-col gap-1">
                                    <span className="text-sm font-medium">
                                      {selectedFacts.length} fact
                                      {selectedFacts.length !== 1
                                        ? "s"
                                        : ""}{" "}
                                      selected
                                    </span>
                                    {videoSuccess && (
                                      <span className="text-xs text-green-600">
                                        ✓ Video generation started!
                                      </span>
                                    )}
                                    {videoError && (
                                      <span className="text-xs text-red-600">
                                        ✗ {videoError}
                                      </span>
                                    )}
                                  </div>
                                  <Button
                                    onClick={handleSubmitVideo}
                                    size="sm"
                                    disabled={
                                      isLoading ||
                                      isGeneratingVideo ||
                                      !storeSessionId
                                    }
                                  >
                                    {isGeneratingVideo ? (
                                      <>
                                        <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                                        Generating...
                                      </>
                                    ) : videoSuccess ? (
                                      "✓ Video Started"
                                    ) : (
                                      "Create Video"
                                    )}
                                  </Button>
                                </div>
                              </AlertDescription>
                            </Alert>
                          </div>
                        </MessageContent>
                      </Message>
                    )}
                    {isGeneratingVideo && (
                      <Message from="assistant">
                        <MessageContent>
                          <div className="flex items-center gap-3">
                            <div className="border-primary h-5 w-5 animate-spin rounded-full border-2 border-t-transparent" />
                            <p>
                              Starting video generation... This may take a few
                              minutes.
                            </p>
                          </div>
                        </MessageContent>
                      </Message>
                    )}
                    {thinkingStatus && (
                      <Message from="assistant">
                        <MessageContent>
                          <div className="space-y-3">
                            <ScriptGenerationChainOfThought
                              isVisible={true}
                              operation={thinkingStatus.operation}
                            />
                            {childAge && childInterest && (
                              <div className="flex items-center justify-center">
                                <Badge variant="secondary" className="text-xs">
                                  Personalizing for {childAge}-year-old
                                  interested in {childInterest}
                                </Badge>
                              </div>
                            )}
                          </div>
                        </MessageContent>
                      </Message>
                    )}
                  </>
                )}
                {error && (
                  <div className="p-4 text-sm text-red-500">
                    Error: {error.message}
                  </div>
                )}
              </ConversationContent>
            </Conversation>
            <div className="shrink-0 border-t p-4">
              <PromptInput
                onSubmit={handleSubmit}
                accept=".pdf,application/pdf"
              >
                <PromptInputBody>
                  <PromptInputAttachments>
                    {(attachment) => (
                      <PromptInputAttachment data={attachment} />
                    )}
                  </PromptInputAttachments>
                  <PromptInputTextarea
                    placeholder={
                      workflowStep === "selection"
                        ? "Review and select facts on the right, then click Submit..."
                        : "Tell me about your student, or share lesson materials..."
                    }
                    disabled={workflowStep === "selection"}
                  />
                </PromptInputBody>
                <PromptInputFooter>
                  <PromptInputActionMenu>
                    <PromptInputActionMenuTrigger>
                      <Paperclip className="size-4" />
                    </PromptInputActionMenuTrigger>
                    <PromptInputActionMenuContent>
                      <PromptInputActionAddAttachments label="Add PDF" />
                    </PromptInputActionMenuContent>
                  </PromptInputActionMenu>
                  <PromptInputSubmit
                    status={isLoading ? "streaming" : undefined}
                    disabled={workflowStep === "selection"}
                  />
                </PromptInputFooter>
              </PromptInput>
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle />

        {/* Document Editor Panel */}
        <ResizablePanel defaultSize={60} minSize={30}>
          <DocumentEditor />
        </ResizablePanel>
      </ResizablePanelGroup>

      {/* Delete confirmation dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Session?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete this session and all associated data
              from the database. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteSession}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
