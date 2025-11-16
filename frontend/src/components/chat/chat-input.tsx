"use client";

import { Button } from "@/components/ui/button";

import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { ArrowUp, BookOpen, GraduationCap, Sparkles } from "lucide-react";

import { useRef, useState } from "react";
import type { KeyboardEvent } from "react";

const PROMPTS = [
  {
    icon: BookOpen,
    text: "Create a lesson plan",
    prompt:
      "Create a lesson plan for [subject] covering [topic] for [grade level] students.",
  },
  {
    icon: GraduationCap,
    text: "Best activities for grade level",
    prompt:
      "What activities work best for [grade level] students learning [subject]?",
  },
  {
    icon: Sparkles,
    text: "Make topic engaging",
    prompt: "How can I make [topic] more engaging for my students?",
  },
];

interface ChatInputProps {
  onSubmit?: (message: string) => void;
}

export default function ChatInput({ onSubmit }: ChatInputProps) {
  const [inputValue, setInputValue] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    if (!inputValue.trim() || !onSubmit) return;

    onSubmit(inputValue.trim());
    setInputValue("");
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handlePromptClick = (prompt: string) => {
    if (inputRef.current) {
      inputRef.current.value = prompt;
      setInputValue(prompt);
      inputRef.current.focus();
      // Auto-submit when prompt is clicked
      if (onSubmit) {
        setTimeout(() => {
          onSubmit(prompt);
          setInputValue("");
          inputRef.current!.value = "";
        }, 100);
      }
    }
  };

  return (
    <div className="flex w-full flex-col gap-4">
      <div className="flex flex-wrap justify-center gap-2">
        {PROMPTS.map((button) => {
          const IconComponent = button.icon;
          return (
            <Button
              key={button.text}
              variant="ghost"
              className="group text-foreground hover:bg-muted/30 dark:bg-muted flex h-auto items-center gap-2 rounded-full border bg-transparent px-3 py-2 text-sm transition-all duration-200"
              onClick={() => handlePromptClick(button.prompt)}
            >
              <IconComponent className="text-muted-foreground group-hover:text-foreground h-4 w-4 transition-colors" />
              <span>{button.text}</span>
            </Button>
          );
        })}
      </div>
      <div className="bg-card border-border flex min-h-[120px] cursor-text flex-col rounded-2xl border shadow-lg">
        <div className="relative max-h-[258px] flex-1 overflow-y-auto">
          <Textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about creating lesson plans..."
            className="text-foreground min-h-[48.4px] w-full resize-none border-0 bg-transparent! p-3 text-[16px] wrap-break-word whitespace-pre-wrap shadow-none transition-[padding] duration-200 ease-in-out outline-none focus-visible:ring-0 focus-visible:ring-offset-0"
          />
        </div>

        <div className="flex min-h-[40px] items-center gap-2 p-2 pb-1">
          <div className="ml-auto flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              className={cn(
                "bg-primary h-6 w-6 cursor-pointer rounded-full transition-all duration-100",
                inputValue && "bg-primary hover:bg-primary/90!",
              )}
              disabled={!inputValue}
              onClick={handleSubmit}
            >
              <ArrowUp className="text-primary-foreground h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
