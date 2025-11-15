import { DashboardHeader } from "@/components/dashboard-header";

export default async function Dashboard() {
  return (
    <div className="flex min-h-screen flex-col">
      <DashboardHeader />
      <div className="flex flex-1 flex-col items-center justify-center">
        <div className="container flex flex-col items-center justify-center gap-4 px-4 py-16">
          <p className="text-muted-foreground">Welcome to your dashboard</p>
        </div>
      </div>
    </div>
  );
}
