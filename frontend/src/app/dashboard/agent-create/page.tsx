"use client";

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
} from "@/components/ai-elements/prompt-input";
import {
  Message,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
import { DocumentEditor } from "./_components/document-editor";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import { useState } from "react";
import { type Fact, type Narration } from "@/types";

type WorkflowStep = "input" | "selection" | "review";

export default function Home() {
  const [documentContent, setDocumentContent] = useState("");
  const [messages, setMessages] = useState<
    { role: "user" | "assistant"; content: string; id?: string }[]
  >([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [workflowStep, setWorkflowStep] = useState<WorkflowStep>("input");
  const [facts, setFacts] = useState<Fact[]>([]);
  const [selectedFacts, setSelectedFacts] = useState<Fact[]>([]);
  const [narration, setNarration] = useState<Narration | null>(null);

  const handleFactToggle = (fact: Fact) => {
    setSelectedFacts((prev) => {
      const exists = prev.some((f) => f.concept === fact.concept);
      if (exists) {
        return prev.filter((f) => f.concept !== fact.concept);
      }
      return [...prev, fact];
    });
  };

  const handleSubmitFacts = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/agent-create", {
        method: "POST",
        body: JSON.stringify({
          messages,
          mode: "narrate",
          selectedFacts,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch response");
      }

      const reader = response.body?.getReader();
      if (!reader) return;

      const decoder = new TextDecoder();
      let accumulatedResponse = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        accumulatedResponse += chunk;
      }

      try {
        const json = JSON.parse(accumulatedResponse) as Narration;
        setNarration(json);
        setWorkflowStep("review");
        setMessages((prev) => [
          ...prev,
          {
            role: "user",
            content: `I confirm these facts:\n\n${selectedFacts
              .map((f) => `- ${f.concept}: ${f.details}`)
              .join("\n")}`,
            id: Date.now().toString() + "-user-confirm",
          },
          {
            role: "assistant",
            content: "Here is the narration based on your selected facts.",
            id: Date.now().toString(),
          },
        ]);
      } catch (e) {
        console.error("Failed to parse narration response", e);
      }
    } catch (e) {
      console.error("Chat error:", e);
      setError(e as Error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (message: { text: string; files: unknown[] }) => {
    if (!message.text.trim()) return;

    const newMessages = [
      ...messages,
      {
        role: "user" as const,
        content: message.text,
        id: Date.now().toString(),
      },
    ];
    setMessages(newMessages);
    setIsLoading(true);
    setError(null);

    // If we are in input mode, we extract facts
    if (workflowStep === "input") {
      try {
        const response = await fetch("/api/agent-create", {
          method: "POST",
          body: JSON.stringify({
            messages: newMessages,
            mode: "extract",
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to fetch response");
        }

        const reader = response.body?.getReader();
        if (!reader) return;

        const decoder = new TextDecoder();
        let accumulatedResponse = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          accumulatedResponse += decoder.decode(value, { stream: true });
        }

        try {
          const json = JSON.parse(accumulatedResponse) as { facts?: Fact[] };
          if (json.facts) {
            setFacts(json.facts);
            setWorkflowStep("selection");
            setMessages((prev) => [
              ...prev,
              {
                role: "assistant",
                content:
                  "I've extracted these facts. Please select the ones you want to keep.",
                id: Date.now().toString(),
              },
            ]);
          }
        } catch (e) {
          console.error("Failed to parse response", e);
        }
      } catch (e) {
        console.error("Chat error:", e);
        setError(e as Error);
      } finally {
        setIsLoading(false);
      }
    } else {
      if (workflowStep === "review") {
        setWorkflowStep("input");
        setFacts([]);
        setSelectedFacts([]);
        setDocumentContent("");
        setNarration(null);

        try {
          const response = await fetch("/api/agent-create", {
            method: "POST",
            body: JSON.stringify({
              messages: newMessages,
              mode: "extract",
            }),
          });

          if (!response.ok) {
            throw new Error("Failed to fetch response");
          }

          const reader = response.body?.getReader();
          if (!reader) return;

          const decoder = new TextDecoder();
          let accumulatedResponse = "";

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            accumulatedResponse += decoder.decode(value, { stream: true });
          }

          try {
            const json = JSON.parse(accumulatedResponse) as { facts?: Fact[] };
            if (json.facts) {
              setFacts(json.facts);
              setWorkflowStep("selection");
              setMessages((prev) => [
                ...prev,
                {
                  role: "assistant",
                  content:
                    "I've extracted these facts. Please select the ones you want to keep.",
                  id: Date.now().toString(),
                },
              ]);
            }
          } catch (e) {
            console.error("Failed to parse response", e);
          }
        } catch (e) {
          console.error("Chat error:", e);
          setError(e as Error);
        } finally {
          setIsLoading(false);
        }
      }
    }
  };

  return (
    <div className="flex h-full max-h-screen w-full flex-col">
      <ResizablePanelGroup direction="horizontal" className="h-full">
        {/* Chat Panel */}
        <ResizablePanel defaultSize={40} minSize={30}>
          <div className="bg-background flex h-full flex-col border-r">
            <div className="flex items-center gap-2 border-b px-4 py-3">
              <h2 className="text-sm font-semibold">Chat</h2>
            </div>
            <Conversation className="flex-1">
              <ConversationContent>
                {messages.length === 0 ? (
                  <ConversationEmptyState
                    title="Start your story"
                    description="Tell me a story or provide information to generate a narration."
                  />
                ) : (
                  <>
                    {messages.map((message, i) => (
                      <Message key={message.id ?? i} from={message.role}>
                        <MessageContent>
                          <MessageResponse>{message.content}</MessageResponse>
                        </MessageContent>
                      </Message>
                    ))}
                  </>
                )}
                {error && (
                  <div className="p-4 text-sm text-red-500">
                    Error: {error.message}
                  </div>
                )}
              </ConversationContent>
            </Conversation>
            <div className="border-t p-4">
              <PromptInput onSubmit={handleSubmit}>
                <PromptInputBody>
                  <PromptInputTextarea
                    placeholder={
                      workflowStep === "selection"
                        ? "Select facts on the right and click Submit..."
                        : "Tell me a story..."
                    }
                    disabled={workflowStep === "selection"}
                  />
                </PromptInputBody>
                <PromptInputFooter>
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
          <DocumentEditor
            content={documentContent}
            onContentChange={setDocumentContent}
            isUpdating={isLoading}
            mode={
              workflowStep === "selection"
                ? "select-facts"
                : workflowStep === "review"
                  ? "edit-narration"
                  : "edit"
            }
            facts={facts}
            selectedFacts={selectedFacts}
            onFactToggle={handleFactToggle}
            onSubmitFacts={handleSubmitFacts}
            narration={narration}
            onNarrationChange={setNarration}
          />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
