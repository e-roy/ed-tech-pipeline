"use client";

import { Message, MessageContent } from "@/components/ai-elements/message";
import { Button } from "@/components/ui/button";

export function ChatWelcome() {
  return (
    <div className="@container flex flex-1 flex-col items-center justify-center px-2 py-4 @sm:px-4 @md:px-6 @lg:px-8">
      <Message from="assistant">
        <MessageContent>
          <div className="space-y-3 @md:space-y-4">
            <div>
              <h3 className="mb-2 text-sm font-semibold @sm:text-base @lg:text-lg">
                Create a Personalized Educational Video
              </h3>
              <p className="text-muted-foreground text-xs leading-relaxed @sm:text-sm">
                I&apos;ll help you create an engaging biology video for your
                student. You can share lesson materials to get started, or tell
                me about your student&apos;s age and interests for
                personalization.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                className="cursor-pointer rounded-full px-3 py-1 text-xs @sm:px-4 @sm:text-sm"
                onClick={() => {
                  const textarea = document.querySelector(
                    'textarea[placeholder*="Tell me about"]',
                  );
                  if (textarea instanceof HTMLTextAreaElement) {
                    textarea.value = "My student is __ years old and loves ___";
                    textarea.focus();
                    // Move cursor to first blank
                    textarea.setSelectionRange(14, 16);
                  }
                }}
                size="sm"
                type="button"
                variant="outline"
              >
                Tell me about the student
              </Button>
              <Button
                className="cursor-pointer rounded-full px-3 py-1 text-xs @sm:px-4 @sm:text-sm"
                onClick={() => {
                  const fileInput = document.querySelector(
                    'input[type="file"][accept*="pdf"]',
                  );
                  if (fileInput instanceof HTMLInputElement) {
                    fileInput.click();
                  }
                }}
                size="sm"
                type="button"
                variant="outline"
              >
                Upload lesson PDF
              </Button>
              <Button
                className="cursor-pointer rounded-full px-3 py-1 text-xs @sm:px-4 @sm:text-sm"
                onClick={() => {
                  const textarea = document.querySelector(
                    'textarea[placeholder*="Tell me about"]',
                  );
                  if (textarea instanceof HTMLTextAreaElement) {
                    textarea.focus();
                  }
                }}
                size="sm"
                type="button"
                variant="outline"
              >
                Paste lesson text
              </Button>
            </div>
          </div>
        </MessageContent>
      </Message>
    </div>
  );
}
