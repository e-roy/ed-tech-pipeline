"use client";

import { type NarrationSegment } from "@/types";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Clock, BookOpen, Hash } from "lucide-react";
import { useAgentCreateStore } from "@/stores/agent-create-store";

export function NarrationEditor() {
  const { narration, setNarration } = useAgentCreateStore();

  if (!narration) return null;

  const handleSegmentChange = (
    index: number,
    field: keyof NarrationSegment,
    value: string | number | string[],
  ) => {
    const newSegments = [...narration.segments];
    newSegments[index] = {
      ...newSegments[index],
      [field]: value,
    } as NarrationSegment;
    setNarration({
      ...narration,
      segments: newSegments,
    });
  };

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="flex flex-col items-center justify-center">
            <Clock className="text-muted-foreground mb-2 size-4" />
            <div className="text-2xl font-bold">
              {narration.total_duration}s
            </div>
            <p className="text-muted-foreground text-xs">Total Duration</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex flex-col items-center justify-center">
            <BookOpen className="text-muted-foreground mb-2 size-4" />
            <div className="text-2xl font-bold">{narration.reading_level}</div>
            <p className="text-muted-foreground text-xs">Reading Level</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex flex-col items-center justify-center">
            <Hash className="text-muted-foreground mb-2 size-4" />
            <div className="text-2xl font-bold">
              {narration.key_terms_count}
            </div>
            <p className="text-muted-foreground text-xs">Key Terms</p>
          </CardContent>
        </Card>
      </div>

      <ScrollArea className="max-h-[calc(100vh-28rem)] flex-1 pr-4">
        <div className="flex flex-col gap-4">
          {narration.segments.map((segment, index) => (
            <Card key={segment.id} className="mt-0 overflow-hidden pt-0">
              <CardHeader className="bg-muted/50 px-4 py-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="bg-background">
                      {index + 1}
                    </Badge>
                    <CardTitle className="text-sm font-medium">
                      {segment.type}
                    </CardTitle>
                  </div>
                  <div className="text-muted-foreground flex items-center gap-2 text-xs">
                    <Clock className="size-3" />
                    <span>{segment.duration}s</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="grid gap-4 px-4">
                <div className="space-y-1.5">
                  <Label
                    htmlFor={`narration-${segment.id}`}
                    className="text-muted-foreground text-xs font-medium"
                  >
                    Narration
                  </Label>
                  <Textarea
                    id={`narration-${segment.id}`}
                    value={segment.narration}
                    onChange={(e) =>
                      handleSegmentChange(index, "narration", e.target.value)
                    }
                    className="min-h-[80px] resize-none text-sm"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label
                    htmlFor={`visual-${segment.id}`}
                    className="text-muted-foreground text-xs font-medium"
                  >
                    Visual Guidance
                  </Label>
                  <Textarea
                    id={`visual-${segment.id}`}
                    value={segment.visual_guidance}
                    onChange={(e) =>
                      handleSegmentChange(
                        index,
                        "visual_guidance",
                        e.target.value,
                      )
                    }
                    className="min-h-[60px] resize-none text-sm"
                  />
                </div>

                <div className="flex flex-wrap items-center gap-2 border-t pt-2">
                  <span className="text-muted-foreground text-xs font-medium">
                    Concepts:
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {segment.key_concepts.map((concept, i) => (
                      <Badge
                        key={i}
                        variant="secondary"
                        className="h-5 px-1.5 text-[10px]"
                      >
                        {concept}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
