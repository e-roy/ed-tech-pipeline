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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "clamp(2rem, 3vh, 3rem)",
          right: "clamp(1rem, 4vw, 4rem)",
          width: "clamp(45px, 3.5vw, 60px)",
          height: "clamp(45px, 3.5vw, 60px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "clamp(1rem, 2vh, 2rem)",
          right: "clamp(10rem, 18vw, 18rem)",
          width: "clamp(40px, 3vw, 50px)",
          height: "clamp(40px, 3vw, 50px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "clamp(8rem, 12vh, 12rem)",
          right: "clamp(1rem, 5vw, 5rem)",
          width: "clamp(50px, 3.8vw, 65px)",
          height: "clamp(50px, 3.8vw, 65px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "clamp(2rem, 4vh, 4rem)",
          left: "clamp(2rem, 5vw, 5rem)",
          width: "clamp(52px, 4vw, 70px)",
          height: "clamp(52px, 4vw, 70px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "clamp(6rem, 10vh, 10rem)",
          left: "clamp(8rem, 14vw, 14rem)",
          width: "clamp(42px, 3.2vw, 55px)",
          height: "clamp(42px, 3.2vw, 55px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "clamp(1rem, 2vh, 2rem)",
          left: "clamp(10rem, 18vw, 18rem)",
          width: "clamp(48px, 3.8vw, 65px)",
          height: "clamp(48px, 3.8vw, 65px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "clamp(4rem, 7vh, 7rem)",
          left: "clamp(6rem, 10vw, 10rem)",
          width: "clamp(44px, 3.4vw, 58px)",
          height: "clamp(44px, 3.4vw, 58px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          bottom: "clamp(2rem, 5vh, 5rem)",
          right: "clamp(2rem, 5vw, 5rem)",
          width: "clamp(55px, 4.2vw, 75px)",
          height: "clamp(55px, 4.2vw, 75px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          bottom: "clamp(1rem, 3vh, 3rem)",
          right: "clamp(10rem, 16vw, 16rem)",
          width: "clamp(46px, 3.5vw, 60px)",
          height: "clamp(46px, 3.5vw, 60px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          bottom: "clamp(4rem, 9vh, 9rem)",
          right: "clamp(6rem, 11vw, 11rem)",
          width: "clamp(50px, 4vw, 68px)",
          height: "clamp(50px, 4vw, 68px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          bottom: "clamp(3rem, 6vh, 6rem)",
          left: "clamp(6rem, 11vw, 11rem)",
          width: "clamp(46px, 3.6vw, 62px)",
          height: "clamp(46px, 3.6vw, 62px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "calc(33.33% + clamp(0rem, 2vh, 2rem))",
          right: "clamp(4rem, 8vw, 8rem)",
          width: "clamp(48px, 3.8vw, 65px)",
          height: "clamp(48px, 3.8vw, 65px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "calc(66.67% - clamp(2rem, 3vh, 3rem))",
          left: "clamp(1rem, 4vw, 4rem)",
          width: "clamp(52px, 4vw, 70px)",
          height: "clamp(52px, 4vw, 70px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "calc(50% - clamp(1rem, 2vh, 2rem))",
          right: "clamp(16rem, 22vw, 22rem)",
          width: "clamp(38px, 3vw, 50px)",
          height: "clamp(38px, 3vw, 50px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          bottom: "calc(33.33% + clamp(1rem, 2vh, 2rem))",
          right: "clamp(20rem, 28vw, 28rem)",
          width: "clamp(42px, 3.2vw, 55px)",
          height: "clamp(42px, 3.2vw, 55px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "clamp(7rem, 11vh, 11rem)",
          right: "clamp(14rem, 24vw, 24rem)",
          width: "clamp(44px, 3.4vw, 58px)",
          height: "clamp(44px, 3.4vw, 58px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "clamp(8rem, 14vh, 14rem)",
          left: "clamp(14rem, 24vw, 24rem)",
          width: "clamp(54px, 4.2vw, 72px)",
          height: "clamp(54px, 4.2vw, 72px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "calc(66.67% - clamp(1rem, 2vh, 2rem))",
          right: "clamp(6rem, 11vw, 11rem)",
          width: "clamp(40px, 3.2vw, 54px)",
          height: "clamp(40px, 3.2vw, 54px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "calc(33.33% - clamp(1rem, 2vh, 2rem))",
          left: "clamp(6rem, 11vw, 11rem)",
          width: "clamp(50px, 3.9vw, 66px)",
          height: "clamp(50px, 3.9vw, 66px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          bottom: "clamp(6rem, 12vh, 12rem)",
          right: "clamp(12rem, 20vw, 20rem)",
          width: "clamp(46px, 3.5vw, 60px)",
          height: "clamp(46px, 3.5vw, 60px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "calc(50% + clamp(1rem, 2vh, 2rem))",
          left: "clamp(3rem, 7vw, 7rem)",
          width: "clamp(42px, 3.3vw, 56px)",
          height: "clamp(42px, 3.3vw, 56px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "calc(75% - clamp(1rem, 2vh, 2rem))",
          right: "clamp(8rem, 15vw, 15rem)",
          width: "clamp(50px, 4vw, 68px)",
          height: "clamp(50px, 4vw, 68px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          bottom: "calc(25% - clamp(1rem, 2vh, 2rem))",
          left: "clamp(14rem, 24vw, 24rem)",
          width: "clamp(40px, 3vw, 52px)",
          height: "clamp(40px, 3vw, 52px)",
          zIndex: 1,
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
        className="text-foreground pointer-events-none absolute hidden opacity-100 lg:block"
        style={{
          top: "calc(25% + clamp(0rem, 1vh, 1rem))",
          right: "clamp(3rem, 7vw, 7rem)",
          width: "clamp(52px, 4vw, 70px)",
          height: "clamp(52px, 4vw, 70px)",
          zIndex: 1,
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
