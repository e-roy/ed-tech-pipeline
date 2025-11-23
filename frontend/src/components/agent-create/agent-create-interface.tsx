"use client";

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
import { Message, MessageContent } from "@/components/ai-elements/message";
import { DocumentEditor } from "@/components/agent-create/editors/document-editor";
import { ChatHeader } from "@/components/agent-create/chat/chat-header";
import { ChatWelcome } from "@/components/agent-create/chat/chat-welcome";
import { ChatMessageList } from "@/components/agent-create/chat/chat-message-list";
import { FactSelectionPrompt } from "@/components/agent-create/prompts/fact-selection-prompt";
import { NarrationReviewPrompt } from "@/components/agent-create/prompts/narration-review-prompt";
import { SessionDeleteDialog } from "@/components/agent-create/dialogs/session-delete-dialog";
import { ChatLoadingSkeleton } from "@/components/agent-create/loading/chat-loading-skeleton";
import { EditorLoadingSkeleton } from "@/components/agent-create/loading/editor-loading-skeleton";
import { useSessionManagement } from "@/components/agent-create/hooks/use-session-management";
import { useVideoGeneration } from "@/components/agent-create/hooks/use-video-generation";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import { useAgentCreateStore } from "@/stores/agent-create-store";
import { useState } from "react";
import { Paperclip } from "lucide-react";
import { useRouter } from "next/navigation";

type AgentCreateInterfaceProps = {
  /**
   * Optional sessionId to load on mount.
   * If provided, the component will load the session data.
   */
  sessionId?: string | null;
};

export function AgentCreateInterface({
  sessionId: externalSessionId,
}: AgentCreateInterfaceProps) {
  const {
    messages: storeMessages,
    isLoading,
    isSessionLoading,
    error,
    workflowStep,
    thinkingStatus,
    handleSubmit,
    sessionId: storeSessionId,
    sessionStatus,
    reset,
    setSessionId,
    facts: storeFacts,
    selectedFacts: storeSelectedFacts,
    narration: storeNarration,
    childAge,
    childInterest,
    showFactSelectionPrompt,
    showNarrationReviewPrompt,
    handleSubmitFacts,
  } = useAgentCreateStore();

  // Only use store data if it matches the expected session
  // This prevents showing stale data when navigating between routes
  const sessionMatches = externalSessionId
    ? externalSessionId === storeSessionId
    : !storeSessionId;

  const messages = sessionMatches ? storeMessages : [];
  const facts = sessionMatches ? storeFacts : [];
  const selectedFacts = sessionMatches ? storeSelectedFacts : [];
  const narration = sessionMatches ? storeNarration : null;

  // Delete session dialog state
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const router = useRouter();

  // Custom hooks
  const {
    copied,
    handleCopySessionId,
    handleClearSession,
    handleDeleteSession: deleteSession,
  } = useSessionManagement({
    externalSessionId,
    storeSessionId,
  });

  const { isGeneratingVideo, videoError, videoSuccess, handleSubmitVideo } =
    useVideoGeneration();

  const displaySessionId = externalSessionId ?? storeSessionId;

  const handleNewChat = () => {
    reset();
    setSessionId(null);
    router.push("/dashboard/create");
  };

  const onCopySessionId = () => {
    if (displaySessionId) {
      void handleCopySessionId(displaySessionId);
    }
  };

  const onDeleteSession = () => {
    if (storeSessionId) {
      deleteSession(storeSessionId);
    }
    setShowDeleteDialog(false);
  };

  const onSubmitVideo = () => {
    if (narration && selectedFacts.length > 0 && storeSessionId) {
      void handleSubmitVideo(narration, selectedFacts, storeSessionId);
    }
  };

  // Show loading skeleton when:
  // 1. Currently loading a session (isSessionLoading = true)
  // 2. OR we have an externalSessionId that doesn't match the store (about to load)
  const willLoadSession =
    externalSessionId && externalSessionId !== storeSessionId;
  const showLoadingSkeleton =
    (isSessionLoading || willLoadSession) && !!externalSessionId;

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
            <ChatHeader
              sessionId={displaySessionId}
              copied={copied}
              onNewChat={handleNewChat}
              onClearSession={handleClearSession}
              onDeleteSession={() => setShowDeleteDialog(true)}
              onCopySessionId={onCopySessionId}
            />
            {showLoadingSkeleton ? (
              <ChatLoadingSkeleton />
            ) : (
              <Conversation className="min-h-0 flex-1">
                <ConversationContent className="flex min-h-full flex-col">
                  {messages.length === 0 ? (
                    <ChatWelcome />
                  ) : (
                    <>
                      <ChatMessageList
                        messages={messages}
                        thinkingStatus={thinkingStatus}
                        childAge={childAge}
                        childInterest={childInterest}
                        error={error}
                      />
                      {showFactSelectionPrompt && facts.length > 0 && (
                        <FactSelectionPrompt
                          factsCount={facts.length}
                          selectedFactsCount={selectedFacts.length}
                          onSubmitFacts={handleSubmitFacts}
                          isLoading={isLoading}
                        />
                      )}
                      {showNarrationReviewPrompt && narration && (
                        <NarrationReviewPrompt
                          narration={narration}
                          sessionStatus={sessionStatus}
                          selectedFactsCount={selectedFacts.length}
                          onSubmitVideo={onSubmitVideo}
                          isGeneratingVideo={isGeneratingVideo}
                          videoSuccess={videoSuccess}
                          videoError={videoError}
                          isLoading={isLoading}
                        />
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
                    </>
                  )}
                </ConversationContent>
              </Conversation>
            )}
            <div className="shrink-0 border-t p-4">
              <PromptInput
                onSubmit={handleSubmit}
                accept=".pdf,application/pdf"
                syncHiddenInput={true}
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
                        : showLoadingSkeleton
                          ? "Loading session..."
                          : "Tell me about your student, or share lesson materials..."
                    }
                    disabled={
                      workflowStep === "selection" || !!showLoadingSkeleton
                    }
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
                    disabled={
                      workflowStep === "selection" || !!showLoadingSkeleton
                    }
                  />
                </PromptInputFooter>
              </PromptInput>
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle />

        {/* Document Editor Panel */}
        <ResizablePanel defaultSize={60} minSize={30}>
          {showLoadingSkeleton ? <EditorLoadingSkeleton /> : <DocumentEditor />}
        </ResizablePanel>
      </ResizablePanelGroup>

      {/* Delete confirmation dialog */}
      <SessionDeleteDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        onConfirm={onDeleteSession}
      />
    </div>
  );
}
