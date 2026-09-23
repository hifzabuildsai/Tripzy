import type { TripIntent } from "@/types/trip";

type TripSignatureProps = {
  intent: TripIntent | null;
};

export default function TripSignature({
  intent,
}: TripSignatureProps) {
  if (!intent) {
    return null;
  }

  const details = [
    intent.destination,
    intent.durationDays
      ? `${intent.durationDays} days`
      : null,
    intent.season
      ? intent.season[0].toUpperCase() +
        intent.season.slice(1)
      : null,
  ].filter(Boolean);

  if (details.length === 0) {
    return null;
  }

  return (
    <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
      {details.map((detail) => (
        <span
          key={detail}
          className={[
            "rounded-full",
            "border",
            "border-black/[0.07]",
            "bg-white/70",
            "px-3.5",
            "py-1.5",
            "text-xs",
            "font-medium",
            "text-neutral-700",
            "shadow-[0_8px_24px_rgba(70,50,30,0.05)]",
            "backdrop-blur-xl",
          ].join(" ")}
        >
          {detail}
        </span>
      ))}
    </div>
  );
}