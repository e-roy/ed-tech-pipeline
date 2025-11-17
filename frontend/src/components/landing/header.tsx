import Link from "next/link";
import { Button } from "@/components/ui/button";

const Header = () => {
  return (
    <header className="border-accent bg-background/95 supports-backdrop-filter:bg-background/60 sticky top-0 z-50 w-full border-b backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link href="/" className="flex items-center space-x-2">
          <span className="text-xl font-bold">AI Ad Video Generator</span>
        </Link>
        <Button asChild variant="default" size="default">
          <Link href="/login">Login</Link>
        </Button>
      </div>
    </header>
  );
};

export default Header;
