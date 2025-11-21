"use client";

import type { FileUIPart } from "ai";
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
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
import { useEffect } from "react";
import { Plus, Paperclip } from "lucide-react";
import { Button } from "@/components/ui/button";

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
  } = useAgentCreateStore();

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
      <ResizablePanelGroup direction="horizontal" className="h-full min-h-0">
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
              {displaySessionId && (
                <p className="text-muted-foreground my-auto text-xs">
                  session id: {displaySessionId}
                </p>
              )}
            </div>
            <Conversation className="min-h-0 flex-1">
              <ConversationContent className="flex min-h-full flex-col">
                {messages.length === 0 ? (
                  <ConversationEmptyState
                    title="Start your story"
                    description="Tell me a story or provide information to generate a narration."
                    className="flex-1"
                  />
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

                      const files: FileUIPart[] =
                        (message.files as FileUIPart[] | undefined) ?? [];
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
                    {thinkingStatus && (
                      <Message from="assistant">
                        <MessageContent>
                          <ScriptGenerationChainOfThought
                            isVisible={true}
                            operation={thinkingStatus.operation}
                          />
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
                        ? "Select facts on the right and click Submit..."
                        : "Tell me a story or attach a PDF..."
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
    </div>
  );
}
