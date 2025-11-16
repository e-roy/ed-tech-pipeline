import { CheckCircle, Shield, User, XCircle } from "lucide-react";

const TrustBar = () => {
  const trustSignals = [
    {
      icon: CheckCircle,
      text: "No Setup Fee",
    },
    {
      icon: Shield,
      text: "100% Scientific Accuracy",
    },
    {
      icon: User,
      text: "Teacher Control",
    },
    {
      icon: XCircle,
      text: "Cancel Anytime",
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
