"use client";

import { useState } from "react";
import Image from "next/image";
import { type ImageAsset } from "@/types";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface Props {
  images: ImageAsset[];
  onApprove: (imageIds: string[]) => void;
  minSelection?: number;
}

export function ImageGrid({ images, onApprove, minSelection = 2 }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const toggleSelect = (imageId: string) => {
    const newSelected = new Set(selected);
    if (newSelected.has(imageId)) {
      newSelected.delete(imageId);
    } else {
      newSelected.add(imageId);
    }
    setSelected(newSelected);
  };

  const handleApprove = () => {
    onApprove(Array.from(selected));
  };

  const totalCost = images.reduce((sum, img) => sum + img.cost, 0);

  return (
    <div>
      <div className="mb-6 grid grid-cols-2 gap-6 md:grid-cols-3">
        {images.map((image) => (
          <Card
            key={image.id}
            className={`relative aspect-square cursor-pointer overflow-hidden transition-all ${
              selected.has(image.id)
                ? "ring-4 ring-blue-500"
                : "hover:ring-2 hover:ring-gray-300"
            }`}
            onClick={() => toggleSelect(image.id)}
          >
            <Image
              src={image.url}
              alt={`Product ${image.view_type}`}
              fill
              className="object-cover"
            />

            <div className="absolute top-2 right-2">
              <Checkbox checked={selected.has(image.id)} />
            </div>

            <div className="absolute right-2 bottom-2 rounded bg-black/70 px-2 py-1 text-xs text-white">
              ${image.cost.toFixed(2)}
            </div>

            <div className="absolute bottom-2 left-2 rounded bg-black/70 px-2 py-1 text-xs text-white capitalize">
              {image.view_type}
            </div>
          </Card>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">
            Selected: {selected.size} of {images.length}
          </p>
          <p className="text-xs text-gray-500">
            Total cost: ${totalCost.toFixed(2)}
          </p>
        </div>

        <Button
          onClick={handleApprove}
          disabled={selected.size < minSelection}
          size="lg"
        >
          Add to Mood Board ({selected.size})
        </Button>
      </div>
    </div>
  );
}
