import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowUpRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

const Hero = () => {
  return (
    <div
      className="border-accent relative flex min-h-[calc(100vh-4rem)] w-full items-center justify-center overflow-hidden border-b"
      style={{
        backgroundImage: "url(/1.jpg)",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      }}
    >
      {/* Graph paper texture overlay for reduced opacity */}
      <div className="pointer-events-none absolute inset-0 bg-white opacity-70" />

      {/* Scattered educational doodles - Set 1: upper right area */}
      <Image
        src="/Doodles/Asset 5.svg"
        alt=""
        width={60}
        height={60}
        className="text-foreground pointer-events-none absolute top-12 right-16 opacity-100"
        style={{
          transform: "rotate(-12deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 23.svg"
        alt=""
        width={50}
        height={50}
        className="text-foreground pointer-events-none absolute top-8 right-72 opacity-100"
        style={{
          transform: "rotate(15deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 8.svg"
        alt=""
        width={65}
        height={65}
        className="text-foreground pointer-events-none absolute top-48 right-20 opacity-100"
        style={{
          transform: "rotate(-18deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />

      {/* Set 1: Upper left area */}
      <Image
        src="/Doodles/Asset 18.svg"
        alt=""
        width={70}
        height={70}
        className="text-foreground pointer-events-none absolute top-16 left-20 opacity-100"
        style={{
          transform: "rotate(-8deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 31.svg"
        alt=""
        width={55}
        height={55}
        className="text-foreground pointer-events-none absolute top-40 left-56 opacity-100"
        style={{
          transform: "rotate(12deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 42.svg"
        alt=""
        width={65}
        height={65}
        className="text-foreground pointer-events-none absolute top-8 left-72 opacity-100"
        style={{
          transform: "rotate(-15deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 25.svg"
        alt=""
        width={58}
        height={58}
        className="text-foreground pointer-events-none absolute top-28 left-40 opacity-100"
        style={{
          transform: "rotate(16deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />

      {/* Set 1: Lower right area */}
      <Image
        src="/Doodles/Asset 56.svg"
        alt=""
        width={75}
        height={75}
        className="text-foreground pointer-events-none absolute right-20 bottom-20 opacity-100"
        style={{
          transform: "rotate(10deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 67.svg"
        alt=""
        width={60}
        height={60}
        className="text-foreground pointer-events-none absolute right-64 bottom-12 opacity-100"
        style={{
          transform: "rotate(-10deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 63.svg"
        alt=""
        width={68}
        height={68}
        className="text-foreground pointer-events-none absolute right-44 bottom-36 opacity-100"
        style={{
          transform: "rotate(13deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />

      {/* Set 1: Lower left area */}
      <Image
        src="/Doodles/Asset 73.svg"
        alt=""
        width={62}
        height={62}
        className="text-foreground pointer-events-none absolute bottom-24 left-44 opacity-100"
        style={{
          transform: "rotate(-14deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />

      {/* Set 1: Center scattered */}
      <Image
        src="/Doodles/Asset 45.svg"
        alt=""
        width={65}
        height={65}
        className="text-foreground pointer-events-none absolute top-1/3 right-32 opacity-100"
        style={{
          transform: "rotate(18deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 52.svg"
        alt=""
        width={70}
        height={70}
        className="text-foreground pointer-events-none absolute top-2/3 left-16 opacity-100"
        style={{
          transform: "rotate(-12deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 61.svg"
        alt=""
        width={50}
        height={50}
        className="text-foreground pointer-events-none absolute top-1/2 right-88 opacity-100"
        style={{
          transform: "rotate(6deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 87.svg"
        alt=""
        width={55}
        height={55}
        className="text-foreground pointer-events-none absolute right-112 bottom-1/3 opacity-100"
        style={{
          transform: "rotate(11deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />

      {/* Set 2: Additional scattered doodles */}
      <Image
        src="/Doodles/Asset 14.svg"
        alt=""
        width={58}
        height={58}
        className="text-foreground pointer-events-none absolute top-44 right-96 opacity-100"
        style={{
          transform: "rotate(-11deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 27.svg"
        alt=""
        width={72}
        height={72}
        className="text-foreground pointer-events-none absolute top-56 left-96 opacity-100"
        style={{
          transform: "rotate(9deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 33.svg"
        alt=""
        width={54}
        height={54}
        className="text-foreground pointer-events-none absolute top-2/3 right-44 opacity-100"
        style={{
          transform: "rotate(-16deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 48.svg"
        alt=""
        width={66}
        height={66}
        className="text-foreground pointer-events-none absolute top-1/3 left-44 opacity-100"
        style={{
          transform: "rotate(14deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 55.svg"
        alt=""
        width={60}
        height={60}
        className="text-foreground pointer-events-none absolute right-80 bottom-48 opacity-100"
        style={{
          transform: "rotate(-13deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 76.svg"
        alt=""
        width={56}
        height={56}
        className="text-foreground pointer-events-none absolute top-1/2 left-28 opacity-100"
        style={{
          transform: "rotate(-8deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 80.svg"
        alt=""
        width={68}
        height={68}
        className="text-foreground pointer-events-none absolute top-3/4 right-60 opacity-100"
        style={{
          transform: "rotate(12deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 74.svg"
        alt=""
        width={52}
        height={52}
        className="text-foreground pointer-events-none absolute bottom-1/4 left-96 opacity-100"
        style={{
          transform: "rotate(-15deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <Image
        src="/Doodles/Asset 77.svg"
        alt=""
        width={70}
        height={70}
        className="text-foreground pointer-events-none absolute top-1/4 right-28 opacity-100"
        style={{
          transform: "rotate(10deg)",
          filter:
            "brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)",
        }}
      />
      <div className="relative z-10 mx-auto flex w-full max-w-(--breakpoint-xl) flex-col items-center justify-between gap-x-10 gap-y-14 px-6 py-12 lg:flex-row lg:py-0">
        <div className="max-w-xl">
          <Badge className="rounded-full border-none py-1">
            AI-Powered Educational Video Generation
          </Badge>
          <h1 className="xs:text-4xl mt-6 max-w-[20ch] text-3xl leading-[1.2]! font-bold tracking-tight sm:text-5xl lg:text-[2.75rem] xl:text-5xl">
            Create Educational Videos Students Actually Watch
          </h1>
          <p className="xs:text-lg mt-6 max-w-[60ch]">
            Transform teaching topics with personalized 60-second videos that
            activate student attention through their interests. Generate
            scientifically accurate, engagement-driven content in under 15
            minutes—no more borrowed generic videos students mentally check out
            from.
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
        <div className="relative aspect-square w-full lg:max-w-lg xl:max-w-xl">
          {/* Hand-drawn sketch border SVG with equal spacing on all sides */}
          <svg
            className="pointer-events-none absolute"
            style={{
              top: "12px",
              left: "12px",
              right: "12px",
              bottom: "12px",
              width: "calc(100% - 24px)",
              height: "calc(100% - 24px)",
            }}
            viewBox="0 0 100 100"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            preserveAspectRatio="none"
          >
            <path
              d="M 2,2 L 98,2 L 98,98 L 2,98 Z"
              stroke="rgb(67, 55, 135)"
              strokeWidth="1"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{
                filter: "url(#sketchy-border)",
              }}
            />
            <defs>
              <filter id="sketchy-border">
                <feTurbulence
                  type="fractalNoise"
                  baseFrequency="2"
                  numOctaves="4"
                  result="noise"
                  seed="1"
                />
                <feDisplacementMap
                  in="SourceGraphic"
                  in2="noise"
                  scale="1.5"
                  xChannelSelector="R"
                  yChannelSelector="G"
                />
              </filter>
            </defs>
          </svg>
          <div
            className="bg-accent absolute overflow-hidden rounded-xl"
            style={{
              top: "32px",
              left: "32px",
              right: "32px",
              bottom: "32px",
              width: "calc(100% - 64px)",
              height: "calc(100% - 64px)",
            }}
          >
            <video
              className="h-full w-full rounded-xl object-cover"
              controls
              preload="metadata"
              playsInline
              muted
              loop
            >
              <source src="/Final_Video.mp4" type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Hero;
