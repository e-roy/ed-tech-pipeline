import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import Image from "next/image";
import { Sparkles, Shield, Zap, DollarSign } from "lucide-react";

const Features = () => {
  const features = [
    {
      icon: Sparkles,
      title: "Interest-Driven Engagement",
      description:
        "Transform student interests into learning activators. Generate personalized videos using topics students care about—from axolotls to space exploration—to trigger situational interest and cognitive activation. Students recognize relevance automatically, maintaining optimal attention.",
    },
    {
      icon: Shield,
      title: "Scientific Accuracy Guaranteed",
      description:
        "Every frame validated by Gemini 1.5 Pro Vision. Multi-agent architecture ensures zero misleading information. Scientific accuracy validation that competitors skip entirely.",
    },
    {
      icon: Zap,
      title: "Teacher Control, AI Speed",
      description:
        "60-second videos ready in under 15 minutes. Strategic approval gates maintain your pedagogical authority while AI handles the technical heavy lifting—you guide the learning.",
    },
    {
      icon: DollarSign,
      title: "Cost-Effective at Scale",
      description:
        "$4-5 per video with hybrid template + AI approach. No more hours searching YouTube or expensive video subscriptions. Unlimited personalization without unlimited costs.",
    },
  ];

  return (
    <section className="border-accent bg-muted/30 w-full border-b py-16">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-muted-foreground text-sm">trusted by middle school science teachers</p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
            Engagement-Driven Videos Built for Student Success
          </h2>
          <p className="text-muted-foreground mt-6 text-lg">
            Stop spending hours searching for the perfect video or settling for
            generic content that students tune out from. Create personalized
            science videos that activate attention naturally through cognitive
            optimization—all while maintaining complete scientific accuracy and
            pedagogical control.
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

        <div className="mt-12 grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-4">
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
