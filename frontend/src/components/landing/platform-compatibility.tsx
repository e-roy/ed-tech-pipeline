import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Image from "next/image";
import { ClipboardList, Presentation, BarChart3, Cloud } from "lucide-react";

const PlatformCompatibility = () => {
  const platforms = [
    {
      icon: ClipboardList,
      title: "For Planning",
      description:
        "Input topics and student interests during lesson planning—videos ready before class starts. Transform prep time into engagement time with 15-minute video creation.",
      uiElements: ["15 min videos", "Student interests"],
      // AI Image Prompt: "Teacher planning with clipboard and student interest notes, educational workflow, monochromatic design, professional"
      imagePrompt:
        "Teacher planning with clipboard and student interest notes, educational workflow, monochromatic design, professional",
    },
    {
      icon: Presentation,
      title: "For Classroom",
      description:
        "Deploy personalized content that maintains cognitive load optimization and student attention. Videos designed to activate engagement naturally through interest-alignment.",
      uiElements: ["Cognitive activation", "Natural engagement"],
      // AI Image Prompt: "Classroom presentation with engaged students, personalized video content, monochromatic, clean design"
      imagePrompt:
        "Classroom presentation with engaged students, personalized video content, monochromatic, clean design",
    },
    {
      icon: BarChart3,
      title: "For Assessment",
      description:
        "Track which interest-aligned videos drive engagement and adjust future content. Understand what activates your students' attention and refine your approach.",
      uiElements: ["Engagement tracking", "Content refinement"],
      // AI Image Prompt: "Educational analytics dashboard showing student engagement metrics, monochromatic design, professional"
      imagePrompt:
        "Educational analytics dashboard showing student engagement metrics, monochromatic design, professional",
    },
    {
      icon: Cloud,
      title: "For Anywhere",
      description:
        "Access your personalized video library across all devices. Cloud-based platform syncs automatically, so your interest-aligned content is always ready when you need it.",
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
            Seamless Integration Into Your Teaching Workflow
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
