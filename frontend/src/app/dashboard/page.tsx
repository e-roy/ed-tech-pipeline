import { auth } from "@/server/auth";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ArrowRight,
  BookOpen,
  BrainCircuit,
  FileText,
  Gamepad2,
  GraduationCap,
  LayoutTemplate,
  Library,
  Upload,
  Wand2,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export default async function Dashboard() {
  const session = await auth();
  const user = session?.user;

  return (
    <div className="flex flex-1 flex-col">
      {/* Hero / Welcome Section */}
      <div className="bg-muted/40 relative overflow-hidden border-b pt-8 pb-12 md:pt-12">
        <div className="container mx-auto px-6 md:px-10">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold tracking-tight md:text-4xl lg:text-5xl">
                Welcome, {user?.name?.split(" ")[0] ?? "Teacher"}!
              </h1>
              <p className="text-muted-foreground max-w-2xl text-lg">
                Create engaging, personalized history videos that speak directly
                to your students&apos; interests.
              </p>
            </div>

            {/* Quick Stats or Date could go here */}
            <div className="hidden md:block">
              <div className="flex -space-x-2 overflow-hidden">
                {/* Placeholder for potential user avatars or class stats */}
              </div>
            </div>
          </div>

          {/* Concept Visualizer - Explains the "How" visually */}
          <div className="mt-12 grid gap-4 md:grid-cols-5 md:gap-0">
            {/* Input 1: Lesson */}
            <div className="bg-background relative z-10 flex flex-col items-center justify-center rounded-lg border p-6 text-center shadow-sm md:rounded-r-none md:border-r-0">
              <div className="mb-3 rounded-full bg-blue-100 p-3 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400">
                <FileText className="h-6 w-6" />
              </div>
              <h3 className="font-semibold">Lesson Plan</h3>
              <p className="text-muted-foreground text-xs">
                Text or PDF Source
              </p>
            </div>

            {/* Connector */}
            <div className="bg-background hidden flex-col items-center justify-center border-y md:flex">
              <div className="bg-border h-px w-full" />
              <span className="bg-muted text-muted-foreground absolute z-20 rounded-full border px-2 py-1 text-xs">
                +
              </span>
            </div>

            {/* Input 2: Student Profile */}
            <div className="bg-background relative z-10 flex flex-col items-center justify-center border p-6 text-center shadow-sm md:border-x-0">
              <div className="mb-3 rounded-full bg-purple-100 p-3 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400">
                <Gamepad2 className="h-6 w-6" />
              </div>
              <h3 className="font-semibold">Student Profile</h3>
              <p className="text-muted-foreground text-xs">Age & Interests</p>
            </div>

            {/* Connector */}
            <div className="bg-background hidden flex-col items-center justify-center border-y md:flex">
              <div className="bg-border h-px w-full" />
              <ArrowRight className="text-muted-foreground absolute z-20 h-5 w-5" />
            </div>

            {/* Output: Video */}
            <div className="bg-primary/5 relative z-10 flex flex-col items-center justify-center rounded-lg border p-6 text-center shadow-sm md:rounded-l-none md:border-l-0">
              <div className="bg-primary/20 text-primary mb-3 rounded-full p-3">
                <Wand2 className="h-6 w-6" />
              </div>
              <h3 className="text-primary font-semibold">Magic Video</h3>
              <p className="text-muted-foreground text-xs">
                Personalized Lesson
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto grid gap-8 px-6 py-12 md:grid-cols-12 md:px-10">
        {/* LEFT COLUMN: Main Actions (Width 8/12) */}
        <div className="space-y-8 md:col-span-8">
          <h2 className="text-2xl font-semibold tracking-tight">
            Start Creating
          </h2>

          <div className="grid gap-6">
            {/* Primary Create Card */}
            <Link href="/dashboard/create" className="group block">
              <Card className="border-primary/20 from-background to-muted hover:border-primary/50 relative overflow-hidden bg-gradient-to-br transition-all hover:shadow-lg">
                <div className="bg-primary/5 group-hover:bg-primary/10 absolute top-0 right-0 h-64 w-64 translate-x-1/3 translate-y-[-20%] rounded-full blur-3xl transition-all" />

                <CardHeader className="relative z-10">
                  <div className="mb-2 flex items-center gap-2">
                    <Badge
                      variant="default"
                      className="bg-primary/90 hover:bg-primary"
                    >
                      Action Required
                    </Badge>
                    <span className="text-muted-foreground text-sm">
                      Estimated time: 2 mins
                    </span>
                  </div>
                  <CardTitle className="flex items-center gap-2 text-2xl">
                    <LayoutTemplate className="text-primary h-6 w-6" />
                    Create New Lesson
                  </CardTitle>
                  <CardDescription className="text-base">
                    Enter your lesson topic or upload a PDF, define your
                    student&apos;s interests, and let AI generate a narrated
                    video.
                  </CardDescription>
                </CardHeader>

                <CardContent className="relative z-10 pt-4">
                  <div className="mb-6 flex flex-wrap gap-2">
                    <Badge variant="outline" className="bg-background/50">
                      <Upload className="mr-1 h-3 w-3" /> PDF Upload
                    </Badge>
                    <Badge variant="outline" className="bg-background/50">
                      <BrainCircuit className="mr-1 h-3 w-3" /> AI Narration
                    </Badge>
                    <Badge variant="outline" className="bg-background/50">
                      <GraduationCap className="mr-1 h-3 w-3" /> Age Adapted
                    </Badge>
                  </div>
                  <div
                    className={cn(
                      buttonVariants({ size: "lg" }),
                      "w-full gap-2 shadow-md md:w-auto",
                    )}
                  >
                    Open Studio <ArrowRight className="h-4 w-4" />
                  </div>
                </CardContent>
              </Card>
            </Link>

            {/* Secondary Assets Card */}
            <Link href="/dashboard/assets" className="group block">
              <Card className="hover:border-primary/50 hover:bg-accent/5 transition-all hover:shadow-md">
                <div className="flex flex-col md:flex-row md:items-center">
                  <CardHeader className="flex-1">
                    <CardTitle className="flex items-center gap-2 text-xl">
                      <Library className="text-muted-foreground h-5 w-5" />
                      Video Library
                    </CardTitle>
                    <CardDescription>
                      Access and manage your previously generated lessons.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-6 md:pt-0 md:pr-6">
                    <div
                      className={cn(
                        buttonVariants({ variant: "outline" }),
                        "w-full gap-2 md:w-auto",
                      )}
                    >
                      View Collection <BookOpen className="h-4 w-4" />
                    </div>
                  </CardContent>
                </div>
              </Card>
            </Link>
          </div>
        </div>

        {/* RIGHT COLUMN: Educational Sidebar (Width 4/12) */}
        <div className="space-y-6 md:col-span-4">
          <h2 className="text-xl font-semibold tracking-tight">
            Did you know?
          </h2>

          {/* Feature 1 */}
          <Card className="bg-muted/30">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Hyper-Personalization</CardTitle>
            </CardHeader>
            <CardContent className="text-muted-foreground text-sm">
              Connecting history to a student&apos;s passion (like
              &quot;Minecraft&quot; or &quot;Soccer&quot;) increases retention
              by up to 40%.
            </CardContent>
          </Card>

          {/* Feature 2 */}
          <Card className="bg-muted/30">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">PDF Support</CardTitle>
            </CardHeader>
            <CardContent className="text-muted-foreground text-sm">
              You can upload entire textbook chapters or lesson plans directly.
              We&apos;ll extract the key facts for you.
            </CardContent>
          </Card>

          {/* Example */}
          <div className="text-muted-foreground rounded-lg border border-dashed p-4 text-sm">
            <p className="text-foreground mb-2 font-medium">
              Try this example:
            </p>
            <ul className="list-disc space-y-1 pl-4">
              <li>
                Topic:{" "}
                <span className="text-foreground">Industrial Revolution</span>
              </li>
              <li>
                Student Age: <span className="text-foreground">12</span>
              </li>
              <li>
                Interest: <span className="text-foreground">Robotics</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
