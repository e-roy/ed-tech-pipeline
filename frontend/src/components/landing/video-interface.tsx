import Image from "next/image";

const VideoInterface = () => {
  return (
    <section className="border-accent bg-background w-full border-b py-16">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Videos that work the way you teach
          </h2>
          <p className="text-muted-foreground mt-6 text-lg">
            Educational videos shouldn&apos;t feel generic or inaccurate. With
            our AI-powered system, every video flows from your learning
            objectives and adapts to your teaching style, helping you stay
            focused and productive.
          </p>
        </div>

        <div className="mt-12">
          {/* AI Image Prompt: "Clean educational video editing interface mockup, monochromatic design, showing script editor with formatting tools, professional and minimal, grayscale color scheme" */}
          <div className="relative mx-auto max-w-5xl">
            <div className="relative aspect-video w-full overflow-hidden rounded-lg border bg-white">
              <Image
                src="/placeholder.svg"
                fill
                alt="Educational video editing interface mockup showing script editor"
                className="object-contain"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default VideoInterface;
