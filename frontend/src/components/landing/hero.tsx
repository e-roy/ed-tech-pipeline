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
        backgroundImage: 'url(/1.jpg)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
    >
      {/* Graph paper texture overlay for reduced opacity */}
      <div className="absolute inset-0 bg-white opacity-70 pointer-events-none" />

      {/* Scattered educational doodles - Set 1: upper right area */}
      <Image src="/Doodles/Asset 5.svg" alt="" width={60} height={60} className="absolute top-12 right-16 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(-12deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 23.svg" alt="" width={50} height={50} className="absolute top-8 right-72 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(15deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 8.svg" alt="" width={65} height={65} className="absolute top-48 right-20 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(-18deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />

      {/* Set 1: Upper left area */}
      <Image src="/Doodles/Asset 18.svg" alt="" width={70} height={70} className="absolute top-16 left-20 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(-8deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 31.svg" alt="" width={55} height={55} className="absolute top-40 left-56 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(12deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 42.svg" alt="" width={65} height={65} className="absolute top-8 left-72 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(-15deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 25.svg" alt="" width={58} height={58} className="absolute top-28 left-40 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(16deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />

      {/* Set 1: Lower right area */}
      <Image src="/Doodles/Asset 56.svg" alt="" width={75} height={75} className="absolute bottom-20 right-20 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(10deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 67.svg" alt="" width={60} height={60} className="absolute bottom-12 right-64 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(-10deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 63.svg" alt="" width={68} height={68} className="absolute bottom-36 right-44 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(13deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />

      {/* Set 1: Lower left area */}
      <Image src="/Doodles/Asset 73.svg" alt="" width={62} height={62} className="absolute bottom-24 left-44 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(-14deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />

      {/* Set 1: Center scattered */}
      <Image src="/Doodles/Asset 45.svg" alt="" width={65} height={65} className="absolute top-1/3 right-32 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(18deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 52.svg" alt="" width={70} height={70} className="absolute top-2/3 left-16 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(-12deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 61.svg" alt="" width={50} height={50} className="absolute top-1/2 right-88 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(6deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 87.svg" alt="" width={55} height={55} className="absolute bottom-1/3 right-112 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(11deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />

      {/* Set 2: Additional scattered doodles */}
      <Image src="/Doodles/Asset 14.svg" alt="" width={58} height={58} className="absolute top-44 right-96 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(-11deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 27.svg" alt="" width={72} height={72} className="absolute top-56 left-96 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(9deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 33.svg" alt="" width={54} height={54} className="absolute top-2/3 right-44 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(-16deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 48.svg" alt="" width={66} height={66} className="absolute top-1/3 left-44 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(14deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 55.svg" alt="" width={60} height={60} className="absolute bottom-48 right-80 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(-13deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 76.svg" alt="" width={56} height={56} className="absolute top-1/2 left-28 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(-8deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 80.svg" alt="" width={68} height={68} className="absolute top-3/4 right-60 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(12deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 74.svg" alt="" width={52} height={52} className="absolute bottom-1/4 left-96 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(-15deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
      <Image src="/Doodles/Asset 77.svg" alt="" width={70} height={70} className="absolute top-1/4 right-28 opacity-100 pointer-events-none text-foreground" style={{transform: 'rotate(10deg)', filter: 'brightness(0) saturate(100%) invert(22%) sepia(43%) saturate(1847%) hue-rotate(226deg) brightness(91%) contrast(91%)'}} />
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
          {/* Hand-drawn sketch border SVG - positioned behind video */}
          <svg
            className="absolute w-full h-full pointer-events-none"
            style={{ left: '-6px', top: '-6px', width: 'calc(100% + 12px)', height: 'calc(100% + 12px)' }}
            viewBox="0 0 400 400"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M 10,10 Q 12,8 15,10 L 385,12 Q 388,10 390,15 L 392,385 Q 390,388 385,390 L 15,388 Q 12,390 10,385 Z"
              stroke="rgb(67, 55, 135)"
              strokeWidth="5"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{
                filter: 'url(#sketchy)',
              }}
            />
            <defs>
              <filter id="sketchy">
                <feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="3" result="noise" />
                <feDisplacementMap in="SourceGraphic" in2="noise" scale="2" />
              </filter>
            </defs>
          </svg>
          <div className="bg-accent relative overflow-hidden rounded-xl h-full w-full">
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
