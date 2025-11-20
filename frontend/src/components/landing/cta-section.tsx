import { Button } from "@/components/ui/button";
import { ArrowUpRight } from "lucide-react";
import Link from "next/link";

const CTASection = () => {
  return (
    <section className="border-accent bg-background w-full border-b py-16">
      <div className="mx-auto max-w-3xl px-6 text-center">
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Ready to Transform How Your Students Engage with Science?
        </h2>
        <p className="text-muted-foreground mt-6 text-lg">
          Join middle school science teachers creating personalized videos that
          activate attention naturally. Your first video takes 15 minutes—stop
          settling for generic content that students tune out from.
        </p>
        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Button
            asChild
            size="lg"
            className="w-full rounded-full bg-black text-white hover:bg-black/90 sm:w-auto"
          >
            <Link href="/login">Get Started Free</Link>
          </Button>
          <Button
            asChild
            size="lg"
            variant="outline"
            className="hover:bg-muted w-full rounded-full border-2 border-black bg-white sm:w-auto"
          >
            <Link href="/login">
              Get Started Free <ArrowUpRight className="ml-2 h-5 w-5" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
};

export default CTASection;
