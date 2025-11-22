"use client";

import { type ProgressUpdate } from "@/types";
import { Progress } from "@/components/ui/progress";
import { Card } from "@/components/ui/card";

interface Props {
  update: ProgressUpdate | null;
  isConnected: boolean;
}

export function ProgressIndicator({ update, isConnected }: Props) {
  if (!update) return null;

  // Calculate progress percentage from completed/total
  const progressPercent = Math.round(
    (update.progress.completed / update.progress.total) * 100,
  );

  // Determine if the process is complete
  const isComplete =
    update.status === "completed" ||
    update.progress.completed === update.progress.total;

  return (
    <Card className="fixed right-4 bottom-4 w-96 p-6 shadow-lg">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          {isComplete ? "Complete!" : "Generating..."}
        </h3>
        <span className="text-sm text-gray-500">{progressPercent}%</span>
      </div>

      <Progress value={progressPercent} className="mb-3" />

      <p className="mb-2 text-sm text-gray-700">{update.message}</p>

      <div className="mb-2 text-xs text-gray-600">
        Stage: {update.progress.stage}
        {update.progress.section && ` (${update.progress.section})`}
      </div>

      {update.cost > 0 && (
        <p className="text-xs text-gray-500">
          Cost so far: ${update.cost.toFixed(2)}
        </p>
      )}

      {update.error && (
        <div className="mt-2 text-sm text-red-600">Error: {update.error}</div>
      )}

      <div className="mt-3 flex items-center">
        <div
          className={`mr-2 h-2 w-2 rounded-full ${
            isConnected ? "bg-green-500" : "bg-red-500"
          }`}
        />
        <span className="text-xs text-gray-500">
          {isConnected ? "Connected" : "Disconnected"}
        </span>
      </div>
    </Card>
  );
}
