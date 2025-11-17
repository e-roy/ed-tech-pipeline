import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import Image from "next/image";
import { Sparkles, Shield, Zap } from "lucide-react";

const Features = () => {
  const features = [
    {
      icon: Sparkles,
      title: "Smart Video Generation",
      description:
        "Quickly create videos from your lesson plans, facts, and objectives. AI handles script, visuals, and narration while you maintain full control at every stage.",
    },
    {
      icon: Shield,
      title: "Scientific Accuracy",
      description:
        "Every visual validated by Gemini AI. Self-healing system ensures scientifically accurate content for your students. Never worry about misleading information.",
    },
    {
      icon: Zap,
      title: "Simple & Flexible",
      description:
        "A tool that fits your teaching style—whether for life science, biology, or general science. Create videos your way, on the fly, and access them anytime.",
    },
  ];

  return (
    <section className="border-accent bg-muted/30 w-full border-b py-16">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-muted-foreground text-sm">earned by users today</p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
            Smarter Videos. One Simple Space to Create, Customize & Share
          </h2>
          <p className="text-muted-foreground mt-6 text-lg">
            Simplify the way you create educational videos. Generate videos
            instantly from your lesson plans, organize them into clear
            categories, and find anything in seconds. Capture ideas in real
            time, stay focused with smart organization, and keep all your videos
            in one place that moves with you.
          </p>
        </div>

        {/* Feature Visualization Image */}
        {/* AI Image Prompt: "Stylized open box with educational icons floating out, representing video generation workflow, monochromatic design, clean and professional" */}
        <div className="relative mx-auto mt-12 h-64 w-full max-w-2xl overflow-hidden rounded-lg border bg-white">
          <Image
            src="/placeholder.svg"
            fill
            alt="Feature visualization showing video generation workflow with educational icons"
            className="object-contain"
          />
        </div>

        <div className="mt-12 grid grid-cols-1 gap-8 md:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Card key={feature.title} className="bg-background">
                <CardHeader>
                  <div className="bg-muted mb-4 flex h-12 w-12 items-center justify-center rounded-lg">
                    <Icon className="h-6 w-6" />
                  </div>
                  <CardTitle>{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-base leading-relaxed">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default Features;
