"use client";

import {
  FormEvent,
  KeyboardEvent,
  useRef,
  useState,
} from "react";

type TripComposerProps = {
  onSubmit?: (message: string) => void | boolean | Promise<void | boolean>;
  disabled?: boolean;
  mode?: "mission" | "clarification";
  initialMessage?: string;
};

const EXAMPLES = [
  "Karachi to Seoul in April 2027 for 6 days with my sister. $2,500 budget. Food, culture, shopping and cafés — relaxed pace.",
  "Plan 5 days from Karachi to Istanbul in September 2027 for two travelers, around $2,000. History and food, not rushed.",
];

export default function TripComposer({
  onSubmit,
  disabled = false,
  mode = "mission",
  initialMessage = "",
}: TripComposerProps) {
  const [message, setMessage] = useState(initialMessage);
  const [submitting, setSubmitting] = useState(false);
  const textareaRef =
    useRef<HTMLTextAreaElement>(null);

  const resizeTextarea = () => {
    const textarea = textareaRef.current;

    if (!textarea) {
      return;
    }

    textarea.style.height = "auto";

    textarea.style.height = `${Math.min(
      textarea.scrollHeight,
      144,
    )}px`;
  };

  const submitMessage = async () => {
    if (!message.trim() || disabled || submitting) {
      return;
    }

    setSubmitting(true);

    try {
      const accepted = await onSubmit?.(message);

      if (accepted === false) {
        return;
      }

      setMessage("");

      requestAnimationFrame(() => {
        const textarea = textareaRef.current;

        if (textarea) {
          textarea.style.height = "auto";
          textarea.focus();
        }
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmit = (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    submitMessage();
  };

  const handleKeyDown = (
    event: KeyboardEvent<HTMLTextAreaElement>,
  ) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      submitMessage();
    }
  };

  const selectExample = (example: string) => {
    setMessage(example);

    requestAnimationFrame(() => {
      resizeTextarea();
      textareaRef.current?.focus();
    });
  };

  const canSubmit =
    message.trim().length > 0 && !disabled && !submitting;

  return (
    <div className="mx-auto w-full max-w-[760px]">
      <form
        onSubmit={handleSubmit}
        className={[
          "group",
          "relative",
          "rounded-[26px]",
          "border",
          "border-black/[0.07]",
          "bg-white/75",
          "p-2.5",
          "shadow-[0_18px_60px_rgba(74,55,35,0.08)]",
          "backdrop-blur-xl",
          "transition-all",
          "duration-300",
          "focus-within:border-black/[0.12]",
          "focus-within:bg-white/90",
          "focus-within:shadow-[0_24px_80px_rgba(74,55,35,0.12)]",
        ].join(" ")}
      >
        <div className="flex items-end gap-2">
          <textarea
            ref={textareaRef}
            value={message}
            disabled={disabled || submitting}
            rows={mode === "mission" ? 3 : 1}
            aria-label="Describe your trip"
            placeholder={mode === "mission" ? "Tell me the whole trip — where, when, who’s going, your budget, pace and what you love…" : "Share all the missing details in one message…"}
            onChange={(event) => {
              setMessage(event.target.value);

              requestAnimationFrame(
                resizeTextarea,
              );
            }}
            onKeyDown={handleKeyDown}
            className={[
              mode === "mission" ? "min-h-[104px]" : "min-h-[54px]",
              "max-h-52",
              "flex-1",
              "resize-none",
              "overflow-y-auto",
              "bg-transparent",
              "px-4",
              "py-[15px]",
              "text-[15px]",
              "leading-6",
              "text-neutral-900",
              "outline-none",
              "placeholder:text-neutral-400",
              "sm:text-base",
              "disabled:cursor-not-allowed",
              "disabled:opacity-50",
            ].join(" ")}
          />

          <button
            type="submit"
            disabled={!canSubmit}
            aria-label={mode === "mission" ? "Give Tripzy this mission" : "Send missing trip details"}
            className={[
              "mb-0.5",
              "flex",
              "h-12",
              "w-12",
              "shrink-0",
              "items-center",
              "justify-center",
              "rounded-full",
              "transition-all",
              "duration-300",
              canSubmit
                ? [
                    "bg-neutral-900",
                    "text-white",
                    "shadow-[0_8px_24px_rgba(0,0,0,0.16)]",
                    "hover:-translate-y-0.5",
                    "hover:scale-[1.03]",
                    "hover:bg-black",
                    "active:translate-y-0",
                    "active:scale-95",
                  ].join(" ")
                : [
                    "cursor-not-allowed",
                    "bg-neutral-200",
                    "text-neutral-400",
                  ].join(" "),
            ].join(" ")}
          >
            <svg
              width="19"
              height="19"
              viewBox="0 0 24 24"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M12 19V5M12 5L6.5 10.5M12 5L17.5 10.5"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </form>

      {mode === "mission" && <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
        <span className="mr-1 text-xs text-neutral-400">
          Try
        </span>

        {EXAMPLES.map((example) => (
          <button
            key={example}
            type="button"
            onClick={() =>
              selectExample(example)
            }
            className={[
              "rounded-full",
              "border",
              "border-black/[0.06]",
              "bg-white/55",
              "px-3.5",
              "py-1.5",
              "text-xs",
              "text-neutral-600",
              "backdrop-blur-md",
              "transition-all",
              "duration-200",
              "hover:-translate-y-0.5",
              "hover:border-black/[0.1]",
              "hover:bg-white/90",
              "hover:text-neutral-900",
            ].join(" ")}
          >
            {example}
          </button>
        ))}
      </div>}

      <p className="mt-3 text-center text-[11px] text-neutral-400">
        {mode === "mission" ? "Write naturally — one detailed message works best" : "Answer naturally — include every missing detail you know"}
      </p>
    </div>
  );
}
