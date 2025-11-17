import { auth } from "@/server/auth";
import { HydrateClient } from "@/trpc/server";
import Header from "@/components/landing/header";
import Hero from "@/components/landing/hero";
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
        </main>
        <Footer />
      </div>
    </HydrateClient>
  );
}
