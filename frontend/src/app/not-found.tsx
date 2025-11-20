import Link from "next/link";
import { Button } from "@/components/ui/button";
import Header from "@/components/landing/header";
import { Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex flex-1 items-center justify-center">
        <div className="container flex flex-col items-center justify-center gap-6 px-6 py-16 text-center">
          <h1 className="text-6xl font-bold tracking-tight sm:text-7xl lg:text-8xl">
            404
          </h1>
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            Page Not Found
          </h2>
          <p className="text-muted-foreground max-w-md text-lg">
            The page you&apos;re looking for doesn&apos;t exist or has been
            moved.
          </p>
          <Button asChild size="lg" className="mt-4">
            <Link href="/">
              <Home className="h-5 w-5" />
              Go Home
            </Link>
          </Button>
        </div>
      </main>
    </div>
  );
}
