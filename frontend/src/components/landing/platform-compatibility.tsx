import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Image from "next/image";
import { Globe, Monitor, Smartphone, Cloud } from "lucide-react";

const PlatformCompatibility = () => {
  const platforms = [
    {
      icon: Smartphone,
      title: "For Mobile",
      description:
        "Review and download videos on the go with fast, secure sync across all your devices. Access your video library instantly from your phone or tablet.",
      uiElements: ["Keep it simple", "Book a Call"],
      // AI Image Prompt: "Hand holding smartphone showing educational video interface, clean and modern, monochromatic design, professional"
      imagePrompt:
        "Hand holding smartphone showing educational video interface, clean and modern, monochromatic design, professional",
    },
    {
      icon: Monitor,
      title: "For Desktop",
      description:
        "Work smarter on desktop. Enjoy seamless syncing, keyboard shortcuts, and distraction-free video creation on Windows or Linux.",
      uiElements: ["Video created", "Folders used"],
      // AI Image Prompt: "Stylized computer mouse with educational theme, desktop interface, monochromatic, clean design"
      imagePrompt:
        "Stylized computer mouse with educational theme, desktop interface, monochromatic, clean design",
    },
    {
      icon: Globe,
      title: "For Web",
      description:
        "Access your videos anywhere with a responsive web app that loads in under 3 seconds. Works on any browser, any device.",
      uiElements: ["Responsive", "Under 3 seconds"],
      // AI Image Prompt: "Circular icon with stylized headset/hat, surrounded by responsive label and speed indicator, educational web platform theme, monochromatic"
      imagePrompt:
        "Circular icon with stylized headset/hat, surrounded by responsive label and speed indicator, educational web platform theme, monochromatic",
    },
    {
      icon: Cloud,
      title: "For Anywhere",
      description:
        "Cloud-based platform that works on any device. Your videos sync automatically, so you can start on one device and finish on another.",
      uiElements: ["Cloud sync", "Multi-device"],
      // AI Image Prompt: "Cloud-based educational platform visualization, multiple devices connected, monochromatic design, clean and professional"
      imagePrompt:
        "Cloud-based educational platform visualization, multiple devices connected, monochromatic design, clean and professional",
    },
  ];

  return (
    <section className="border-accent bg-muted/30 w-full border-b py-16">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto mb-12 max-w-3xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Videos. Education. Clarity. Wherever you teach.
          </h2>
        </div>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {platforms.map((platform) => {
            const Icon = platform.icon;
            return (
              <Card
                key={platform.title}
                className="bg-background overflow-hidden"
              >
                <div className="bg-muted relative h-48 w-full">
                  {/* AI Image Placeholder */}
                  {/* Prompt: {platform.imagePrompt} */}
                  <Image
                    src="/placeholder.svg"
                    fill
                    alt={`${platform.title} platform representation`}
                    className="object-cover"
                  />
                </div>
                <CardHeader>
                  <div className="mb-2 flex items-center gap-2">
                    <div className="bg-muted flex h-10 w-10 items-center justify-center rounded-lg">
                      <Icon className="h-5 w-5" />
                    </div>
                    <CardTitle>{platform.title}</CardTitle>
                  </div>
                  {platform.uiElements && (
                    <div className="flex flex-wrap gap-2">
                      {platform.uiElements.map((element) => (
                        <Badge
                          key={element}
                          variant="outline"
                          className="text-xs"
                        >
                          {element}
                        </Badge>
                      ))}
                    </div>
                  )}
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-base">
                    {platform.description}
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

export default PlatformCompatibility;
