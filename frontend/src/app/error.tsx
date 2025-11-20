"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import Header from "@/components/landing/header";
import { Home, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/trpc/react";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  const [hasReported, setHasReported] = useState(false);
  const [isReporting, setIsReporting] = useState(false);

  const reportErrorMutation = api.errorReports.reportError.useMutation({
    onSuccess: () => {
      toast.success("Error reported successfully. Thank you for your feedback!");
      setHasReported(true);
      setIsReporting(false);
    },
    onError: (error) => {
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to report error. Please try again later.",
      );
      setIsReporting(false);
    },
  });

  const handleReportError = async () => {
    if (hasReported || isReporting) return;

    setIsReporting(true);

    try {
      // Extract safe error information
      const errorName = error.name || "UnknownError";
      const errorMessage = error.message || "An unexpected error occurred";
      const url = typeof window !== "undefined" ? window.location.href : "";
      const userAgent =
        typeof window !== "undefined" ? window.navigator.userAgent : "";

      await reportErrorMutation.mutateAsync({
        error_name: errorName,
        error_message: errorMessage,
        url: url || undefined,
        user_agent: userAgent || undefined,
      });
    } catch (err) {
      // Error handling is done in onError callback
      console.error("Failed to report error:", err);
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex flex-1 items-center justify-center">
        <div className="container flex flex-col items-center justify-center gap-6 px-6 py-16 text-center">
          <h1 className="text-6xl font-bold tracking-tight sm:text-7xl lg:text-8xl">
            Oops!
          </h1>
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            Something went wrong
          </h2>
          <p className="text-muted-foreground max-w-md text-lg">
            We&apos;re sorry, but something unexpected happened. Our team has been
            notified and we&apos;re working to fix the issue.
          </p>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row">
            <Button asChild size="lg" variant="default">
              <Link href="/">
                <Home className="mr-2 h-5 w-5" />
                Go Home
              </Link>
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={handleReportError}
              disabled={hasReported || isReporting}
            >
              <AlertCircle className="mr-2 h-5 w-5" />
              {isReporting
                ? "Reporting..."
                : hasReported
                  ? "Error Reported"
                  : "Report Issue"}
            </Button>
            <Button size="lg" variant="ghost" onClick={reset}>
              Try Again
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}

