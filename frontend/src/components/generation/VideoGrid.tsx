"use client";

import { useState } from "react";
import { type VideoAsset } from "@/types";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface Props {
  clips: VideoAsset[];
  onApprove: (clipIds: string[], order: string[]) => void;
  minSelection?: number;
}

export function VideoGrid({ clips, onApprove, minSelection = 2 }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const toggleSelect = (clipId: string) => {
    const newSelected = new Set(selected);
    if (newSelected.has(clipId)) {
      newSelected.delete(clipId);
    } else {
      newSelected.add(clipId);
    }
    setSelected(newSelected);
  };

  const handleApprove = () => {
    const selectedIds = Array.from(selected);
    onApprove(selectedIds, selectedIds); // Order same as selection for now
  };

  const totalCost = clips.reduce((sum, clip) => sum + clip.cost, 0);
  const totalDuration = clips
    .filter((c) => selected.has(c.id))
    .reduce((sum, clip) => sum + clip.duration, 0);

  return (
    <div>
      <div className="mb-6 grid grid-cols-1 gap-6 md:grid-cols-2">
        {clips.map((clip) => (
          <Card
            key={clip.id}
            className={`relative cursor-pointer overflow-hidden transition-all ${
              selected.has(clip.id)
                ? "ring-4 ring-blue-500"
                : "hover:ring-2 hover:ring-gray-300"
            }`}
            onClick={() => toggleSelect(clip.id)}
          >
            <video
              src={clip.url}
              controls
              className="aspect-video w-full"
              onClick={(e) => e.stopPropagation()}
            />

            <div className="absolute top-2 right-2">
              <Checkbox checked={selected.has(clip.id)} />
            </div>

            <div className="p-4">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">
                  Duration: {clip.duration.toFixed(1)}s
                </span>
                <span className="text-gray-600">
                  Cost: ${clip.cost.toFixed(2)}
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">
            Selected: {selected.size} of {clips.length}
          </p>
          <p className="text-xs text-gray-500">
            Total duration: {totalDuration.toFixed(1)}s | Cost: $
            {totalCost.toFixed(2)}
          </p>
        </div>

        <Button
          onClick={handleApprove}
          disabled={selected.size < minSelection}
          size="lg"
        >
          Continue to Final Composition
        </Button>
      </div>
    </div>
  );
}
