"use client";

import { Button } from "@/components/ui/button";
import { AssetType } from "@/lib/types/storage";
import { cn } from "@/lib/utils";

interface ContentFiltersProps {
  selectedFilter: AssetType | "all";
  onFilterChange: (filter: AssetType | "all") => void;
}

const filters: Array<{ value: AssetType | "all"; label: string }> = [
  { value: "all", label: "All" },
  { value: AssetType.IMAGES, label: "Images" },
  { value: AssetType.VIDEOS, label: "Videos" },
  { value: AssetType.AUDIO, label: "Audio" },
  { value: AssetType.FINAL, label: "Final Videos" },
];

export function ContentFilters({
  selectedFilter,
  onFilterChange,
}: ContentFiltersProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {filters.map((filter) => (
        <Button
          key={filter.value}
          variant={selectedFilter === filter.value ? "default" : "outline"}
          size="sm"
          onClick={() => onFilterChange(filter.value)}
          className={cn(
            "transition-all",
            selectedFilter === filter.value && "shadow-sm"
          )}
        >
          {filter.label}
        </Button>
      ))}
    </div>
  );
}


