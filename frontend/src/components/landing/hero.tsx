import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowUpRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

const Hero = () => {
  return (
    <div className="border-accent flex min-h-[calc(100vh-4rem)] w-full items-center justify-center overflow-hidden border-b">
      <div className="mx-auto flex w-full max-w-(--breakpoint-xl) flex-col items-center justify-between gap-x-10 gap-y-14 px-6 py-12 lg:flex-row lg:py-0">
        <div className="max-w-xl">
          <Badge className="rounded-full border-none py-1">
            AI-Powered Video Generation
          </Badge>
          <h1 className="xs:text-4xl mt-6 max-w-[20ch] text-3xl leading-[1.2]! font-bold tracking-tight sm:text-5xl lg:text-[2.75rem] xl:text-5xl">
            Create Professional Ad Videos with AI
          </h1>
          <p className="xs:text-lg mt-6 max-w-[60ch]">
            Generate stunning 8-12 second product advertisement videos with
            visual consistency, full user control, and professional output. Our
            AI-powered pipeline creates publication-ready videos in minutes.
          </p>
          <div className="mt-12 flex flex-col items-center gap-4 sm:flex-row">
            <Button
              asChild
              size="lg"
              className="w-full rounded-full text-base sm:w-auto"
            >
              <Link href="/login">
                Get Started <ArrowUpRight className="h-5! w-5!" />
              </Link>
            </Button>
          </div>
        </div>
        <div className="bg-accent relative aspect-square w-full rounded-xl lg:max-w-lg xl:max-w-xl">
          <Image
            src="/placeholder.svg"
            fill
            alt="AI-generated ad video preview"
            className="rounded-xl object-cover"
          />
        </div>
      </div>
    </div>
  );
};

export default Hero;
