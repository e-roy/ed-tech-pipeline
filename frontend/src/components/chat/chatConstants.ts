import { BookOpen, GraduationCap, Sparkles, type LucideIcon } from "lucide-react";

export interface ChatPrompt {
  icon: LucideIcon;
  text: string;
  prompt: string;
}

export const PROMPTS: ChatPrompt[] = [
  {
    icon: BookOpen,
    text: "Create a lesson plan",
    prompt:
      "Create a lesson plan for [subject] covering [topic] for [grade level] students.",
  },
  {
    icon: GraduationCap,
    text: "Best activities for grade level",
    prompt:
      "What activities work best for [grade level] students learning [subject]?",
  },
  {
    icon: Sparkles,
    text: "Make topic engaging",
    prompt: "How can I make [topic] more engaging for my students?",
  },
];

