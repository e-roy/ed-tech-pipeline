const VideoInterface = () => {
  return (
    <section className="border-accent bg-background w-full border-b py-16">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Personalized Learning Through Interest-Aligned Content
          </h2>
          <p className="text-muted-foreground mt-6 text-lg">
            Stop settling for generic YouTube videos that students instantly
            recognize and disengage from. Input your topic, learning objectives,
            and student interests (like axolotls or gaming), and our AI creates
            videos where students see themselves in the material—triggering
            natural attention through cognitive activation, not entertainment
            gimmicks.
          </p>
        </div>

        <div className="mt-12">
          <div className="relative mx-auto max-w-5xl">
            <div className="relative aspect-video w-full overflow-hidden rounded-lg border bg-black">
              <video
                className="h-full w-full object-contain"
                controls
                preload="metadata"
                playsInline
              >
                <source src="/Final_Video.mp4" type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default VideoInterface;
