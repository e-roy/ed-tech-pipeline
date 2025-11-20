import { ContentGallery } from "@/components/content/ContentGallery";

export default function AssetsPage() {
  return (
    <div className="flex h-full flex-col p-4">
      <div className="mb-4">
        <h1 className="text-2xl font-semibold">Assets</h1>
        <p className="text-muted-foreground text-sm">
          Browse and manage your generated assets
        </p>
      </div>
      <ContentGallery />
    </div>
  );
}

