type Props = {
  params: Promise<{ id: string }>;
};

export default async function HistoryPage({ params }: Props) {
  const { id } = await params;
  
  return (
    <div className="flex h-full items-center justify-center p-4">
      <p className="text-muted-foreground">History page for session: {id}</p>
    </div>
  );
}

