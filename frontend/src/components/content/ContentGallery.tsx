"use client";

import { api } from "@/trpc/react";
import { ContentCard } from "./ContentCard";
import { ContentFilters } from "./ContentFilters";
import type { AssetType } from "@/types/storage";
import { useState } from "react";
import {
  Empty,
  EmptyHeader,
  EmptyTitle,
  EmptyDescription,
} from "@/components/ui/empty";
import { Skeleton } from "@/components/ui/skeleton";
import { getAssetTypeFromKey } from "./utils";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";

const ITEMS_PER_PAGE = 20;

export function ContentGallery() {
  const [selectedFilter, setSelectedFilter] = useState<AssetType | "all">(
    "all",
  );
  const [currentPage, setCurrentPage] = useState(1);

  // Fetch all files from output folder
  const { data, isLoading, refetch } = api.storage.listFiles.useQuery({
    folder: "output",
    limit: 1000, // Get all files for client-side filtering
    offset: 0,
  });

  // Delete mutation
  const deleteMutation = api.storage.deleteFile.useMutation({
    onSuccess: () => {
      void refetch();
    },
  });

  // Filter files client-side
  const filteredFiles =
    data?.files.filter((file) => {
      // Filter out JSON files since they are not media files
      if (file.key.toLowerCase().endsWith('.json')) return false;
      
      if (selectedFilter === "all") return true;

      // Extract asset type from key
      const assetType = getAssetTypeFromKey(file.key);
      if (!assetType) return false;
      return assetType === selectedFilter;
    }) ?? [];

  // Pagination
  const totalPages = Math.ceil(filteredFiles.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginatedFiles = filteredFiles.slice(
    startIndex,
    startIndex + ITEMS_PER_PAGE,
  );

  // Reset to page 1 when filter changes
  const handleFilterChange = (filter: AssetType | "all") => {
    setSelectedFilter(filter);
    setCurrentPage(1);
  };

  const handleDelete = async (fileKey: string) => {
    await deleteMutation.mutateAsync({ file_key: fileKey });
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="aspect-video rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 overflow-y-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Content Library</h2>
          <p className="text-muted-foreground text-sm">
            {filteredFiles.length} file{filteredFiles.length !== 1 ? "s" : ""}
            {selectedFilter !== "all" && ` in ${selectedFilter}`}
          </p>
        </div>
        <ContentFilters
          selectedFilter={selectedFilter}
          onFilterChange={handleFilterChange}
        />
      </div>

      {filteredFiles.length === 0 ? (
        <Empty>
          <EmptyHeader>
            <EmptyTitle>No files found</EmptyTitle>
            <EmptyDescription>
              {selectedFilter === "all"
                ? "You haven't uploaded any files yet."
                : `No ${selectedFilter} files found.`}
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {paginatedFiles.map((file) => (
              <ContentCard
                key={file.key}
                file={file}
                onDelete={() => handleDelete(file.key)}
                isDeleting={deleteMutation.isPending}
              />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <span className="text-muted-foreground text-sm">
                Page {currentPage} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
