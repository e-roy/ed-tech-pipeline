import { Clock, Shield, User, DollarSign } from "lucide-react";

const TrustBar = () => {
  const trustSignals = [
    {
      icon: Clock,
      text: "Videos in 15 Minutes",
    },
    {
      icon: Shield,
      text: "100% Scientific Accuracy",
    },
    {
      icon: DollarSign,
      text: "$4-5 Per Video",
    },
    {
      icon: User,
      text: "Full Teacher Control",
    },
  ];

  return (
    <section className="border-accent bg-muted/30 w-full border-b py-8">
      <div className="mx-auto max-w-7xl px-6">
        <div className="flex flex-wrap items-center justify-center gap-8 md:gap-12">
          {trustSignals.map((signal) => {
            const Icon = signal.icon;
            return (
              <div
                key={signal.text}
                className="flex items-center gap-2 text-sm font-medium"
              >
                <Icon className="h-5 w-5" />
                <span>{signal.text}</span>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default TrustBar;
