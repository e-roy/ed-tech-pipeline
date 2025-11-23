"use client";

import { Skeleton } from "@/components/ui/skeleton";

export function EditorLoadingSkeleton() {
  return (
    <div className="flex h-full flex-col p-6">
      {/* Header */}
      <div className="mb-6 space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-64" />
      </div>

      {/* Content */}
      <div className="space-y-4">
        <div className="space-y-2">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-24 w-full rounded-lg" />
        </div>

        <div className="space-y-2">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-24 w-full rounded-lg" />
        </div>

        <div className="space-y-2">
          <Skeleton className="h-6 w-36" />
          <Skeleton className="h-24 w-full rounded-lg" />
        </div>
      </div>

      {/* Action buttons */}
      <div className="mt-auto flex gap-2">
        <Skeleton className="h-10 w-32" />
        <Skeleton className="h-10 w-24" />
      </div>
    </div>
  );
}

