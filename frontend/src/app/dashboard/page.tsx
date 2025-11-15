import { DashboardHeader } from "@/components/dashboard-header";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ContentGallery } from "@/components/content/ContentGallery";

export default async function Dashboard() {
  return (
    <div className="flex min-h-screen flex-col">
      <DashboardHeader />
      <div className="flex flex-1 flex-col">
        <div className="container flex flex-col gap-6 px-4 py-8">
          <Tabs defaultValue="overview" className="w-full">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="content">Content Library</TabsTrigger>
            </TabsList>
            <TabsContent value="overview" className="mt-6">
              <div className="flex flex-col items-center justify-center gap-4 py-16">
                <p className="text-muted-foreground">Welcome to your dashboard</p>
              </div>
            </TabsContent>
            <TabsContent value="content" className="mt-6">
              <ContentGallery />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
