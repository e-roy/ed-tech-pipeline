import { auth } from "@/server/auth";
import { HydrateClient } from "@/trpc/server";
import Header from "@/components/landing/header";
import Hero from "@/components/landing/hero";
import TrustBar from "@/components/landing/trust-bar";
import PlatformCompatibility from "@/components/landing/platform-compatibility";
import VideoInterface from "@/components/landing/video-interface";
import Features from "@/components/landing/features";
import CTASection from "@/components/landing/cta-section";
import Footer from "@/components/landing/footer";

export default async function Home() {
  const session = await auth();

  if (session?.user) {
  }

  return (
    <HydrateClient>
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="flex-1">
          <Hero />
          <TrustBar />
          <PlatformCompatibility />
          <VideoInterface />
          <Features />
          <CTASection />
        </main>
        <Footer />
      </div>
    </HydrateClient>
  );
}
