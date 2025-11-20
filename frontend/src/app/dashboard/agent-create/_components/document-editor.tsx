"use client";

import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { FileTextIcon, CheckCircle2, Circle } from "lucide-react";
import type { HTMLAttributes } from "react";
import { type Fact, type Narration } from "@/types";
import { Button } from "@/components/ui/button";
import { NarrationEditor } from "./narration-editor";

export type DocumentEditorProps = HTMLAttributes<HTMLDivElement> & {
  content: string;
  onContentChange: (content: string) => void;
  isUpdating?: boolean;
  mode?: "edit" | "select-facts" | "edit-narration";
  facts?: Fact[];
  selectedFacts?: Fact[];
  onFactToggle?: (fact: Fact) => void;
  onSubmitFacts?: () => void;
  narration?: Narration | null;
  onNarrationChange?: (narration: Narration) => void;
};

export function DocumentEditor({
  content,
  onContentChange,
  isUpdating = false,
  mode = "edit",
  facts = [],
  selectedFacts = [],
  onFactToggle,
  onSubmitFacts,
  narration,
  onNarrationChange,
  className,
  ...props
}: DocumentEditorProps) {
  return (
    <div
      className={cn("bg-background flex h-full flex-col border-l", className)}
      {...props}
    >
      <div className="flex items-center gap-2 border-b px-4 py-3">
        <FileTextIcon className="text-muted-foreground size-5" />
        <h2 className="text-sm font-semibold">
          {mode === "edit"
            ? "Create Educational Video"
            : mode === "select-facts"
              ? "Select Facts"
              : "Edit Narration"}
        </h2>
        {isUpdating && (
          <span className="text-muted-foreground ml-auto text-xs">
            Updating...
          </span>
        )}
        {mode === "select-facts" && onSubmitFacts && (
          <Button
            size="sm"
            onClick={onSubmitFacts}
            className="ml-auto"
            disabled={selectedFacts.length === 0 || isUpdating}
          >
            Submit Selected Facts ({selectedFacts.length})
          </Button>
        )}
      </div>
      <ScrollArea className="flex-1">
        <div className="h-full p-4">
          {mode === "edit" ? (
            <Textarea
              value={content}
              onChange={(e) => onContentChange(e.target.value)}
              placeholder="Your markdown document content will appear here. Use the chat to edit it."
              className="min-h-[calc(100vh-8rem)] resize-none border-0 bg-transparent font-mono text-sm focus-visible:ring-0"
              disabled={isUpdating}
            />
          ) : mode === "select-facts" ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {facts.map((fact, index) => {
                const isSelected = selectedFacts.some(
                  (f) => f.concept === fact.concept,
                );
                return (
                  <div
                    key={index}
                    onClick={() => onFactToggle?.(fact)}
                    className={cn(
                      "hover:bg-accent cursor-pointer rounded-lg border p-4 transition-all",
                      isSelected
                        ? "border-primary bg-accent"
                        : "border-border bg-card",
                    )}
                  >
                    <div className="mb-2 flex items-start justify-between gap-2">
                      <h3 className="text-sm font-semibold">{fact.concept}</h3>
                      {isSelected ? (
                        <CheckCircle2 className="text-primary size-4" />
                      ) : (
                        <Circle className="text-muted-foreground size-4" />
                      )}
                    </div>
                    <p className="text-muted-foreground text-sm">
                      {fact.details}
                    </p>
                    <div className="text-muted-foreground mt-2 text-xs">
                      Confidence: {Math.round(fact.confidence * 100)}%
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            narration &&
            onNarrationChange && (
              <NarrationEditor
                narration={narration}
                onNarrationChange={onNarrationChange}
              />
            )
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
