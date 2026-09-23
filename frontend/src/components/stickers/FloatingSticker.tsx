"use client";

import {
  useEffect,
  useRef,
} from "react";

import Image from "next/image";

import type { StickerMotionConfig } from "@/lib/motion";
import type { StickerAsset } from "@/types/sticker";

type FloatingStickerProps = {
  sticker: StickerAsset;
  motionConfig: StickerMotionConfig;
  onCycleComplete: () => void;
};

const DEPTH_SIZE_CLASS = {
  far: [
    "w-[100px]",
    "sm:w-[120px]",
    "md:w-[140px]",
    "lg:w-[clamp(145px,10vw,185px)]",
  ].join(" "),

  mid: [
    "w-[115px]",
    "sm:w-[140px]",
    "md:w-[165px]",
    "lg:w-[clamp(170px,12vw,225px)]",
  ].join(" "),

  near: [
    "w-[130px]",
    "sm:w-[160px]",
    "md:w-[190px]",
    "lg:w-[clamp(195px,14vw,260px)]",
  ].join(" "),
} as const;

const PARTICLES = Array.from(
  { length: 8 },
  (_, index) => index,
);

function createJourneyTransform(
  driftX: number,
  driftY: number,
  scale: number,
  rotation: number,
): string {
  return [
    "translate(-50%, -50%)",
    `translate3d(${driftX}vw, ${driftY}vh, 0)`,
    `scale(${scale})`,
    `rotate(${rotation}deg)`,
  ].join(" ");
}

export default function FloatingSticker({
  sticker,
  motionConfig,
  onCycleComplete,
}: FloatingStickerProps) {
  const stickerRef =
    useRef<HTMLDivElement>(null);

  const interactiveRef =
    useRef<HTMLDivElement>(null);

  const burstRingRef =
    useRef<HTMLDivElement>(null);

  const particleContainerRef =
    useRef<HTMLDivElement>(null);

  const journeyAnimationRef =
    useRef<Animation | null>(null);

  const completionCallbackRef =
    useRef(onCycleComplete);

  const hasCompletedRef =
    useRef(false);

  const isPoppingRef =
    useRef(false);

  const pointerFrameRef =
    useRef<number | null>(null);

  const {
    depth,
    startX,
    startY,
    driftX,
    driftY,
    startScale,
    endScale,
    startRotation,
    endRotation,
    duration,
    delay,
    maxOpacity,
  } = motionConfig;

  useEffect(() => {
    completionCallbackRef.current =
      onCycleComplete;
  }, [onCycleComplete]);

  useEffect(() => {
    const node = stickerRef.current;

    if (!node) {
      return;
    }

    const reduceMotion =
      window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches;

    if (reduceMotion) {
      node.style.opacity =
        String(maxOpacity);

      node.style.transform =
        createJourneyTransform(
          0,
          0,
          1,
          startRotation,
        );

      return;
    }

    let cancelled = false;

    const animation = node.animate(
      [
        {
          offset: 0,
          opacity: 0,
          transform:
            createJourneyTransform(
              0,
              0,
              startScale,
              startRotation,
            ),
        },

        {
          offset: 0.08,
          opacity: maxOpacity,
          transform:
            createJourneyTransform(
              driftX * 0.08,
              driftY * 0.08,
              startScale * 1.035,
              startRotation * 0.9,
            ),
        },

        {
          offset: 0.68,
          opacity: maxOpacity,
          transform:
            createJourneyTransform(
              driftX * 0.68,
              driftY * 0.68,
              startScale +
                (endScale - startScale) *
                  0.68,
              startRotation +
                (endRotation -
                  startRotation) *
                  0.68,
            ),
        },

        {
          offset: 0.91,
          opacity: maxOpacity,
          transform:
            createJourneyTransform(
              driftX,
              driftY,
              endScale,
              endRotation,
            ),
        },

        {
          offset: 1,
          opacity: 0,
          transform:
            createJourneyTransform(
              driftX * 1.06,
              driftY * 1.06,
              endScale * 1.035,
              endRotation,
            ),
        },
      ],
      {
        duration: duration * 1000,
        delay: delay * 1000,
        easing:
          "cubic-bezier(0.37, 0, 0.23, 1)",
        fill: "forwards",
      },
    );

    journeyAnimationRef.current =
      animation;

    animation.finished
      .then(() => {
        if (
          !cancelled &&
          !hasCompletedRef.current
        ) {
          hasCompletedRef.current = true;

          completionCallbackRef.current();
        }
      })
      .catch(() => {});

    return () => {
      cancelled = true;

      animation.cancel();

      if (
        pointerFrameRef.current !== null
      ) {
        cancelAnimationFrame(
          pointerFrameRef.current,
        );
      }
    };
  }, [
    delay,
    driftX,
    driftY,
    duration,
    endRotation,
    endScale,
    maxOpacity,
    startRotation,
    startScale,
  ]);

  const handlePointerEnter = () => {
    if (isPoppingRef.current) {
      return;
    }

    journeyAnimationRef.current?.pause();

    const interactive =
      interactiveRef.current;

    if (!interactive) {
      return;
    }

    interactive.style.filter =
      "drop-shadow(0 22px 30px rgba(60, 45, 30, 0.16))";

    interactive.style.transition =
      "filter 220ms ease";
  };

  const handlePointerMove = (
    event: React.PointerEvent<HTMLDivElement>,
  ) => {
    if (isPoppingRef.current) {
      return;
    }

    const interactive =
      interactiveRef.current;

    if (!interactive) {
      return;
    }

    const rect =
      event.currentTarget.getBoundingClientRect();

    const normalizedX =
      ((event.clientX - rect.left) /
        rect.width -
        0.5) *
      2;

    const normalizedY =
      ((event.clientY - rect.top) /
        rect.height -
        0.5) *
      2;

    const rotateY = normalizedX * 6;
    const rotateX = normalizedY * -6;

    const translateX =
      normalizedX * 8;

    const translateY =
      normalizedY * 8;

    if (
      pointerFrameRef.current !== null
    ) {
      cancelAnimationFrame(
        pointerFrameRef.current,
      );
    }

    pointerFrameRef.current =
      requestAnimationFrame(() => {
        interactive.style.transform = [
          "perspective(700px)",
          `translate3d(${translateX}px, ${translateY}px, 18px)`,
          `rotateX(${rotateX}deg)`,
          `rotateY(${rotateY}deg)`,
          "scale(1.045)",
        ].join(" ");
      });
  };

  const handlePointerLeave = () => {
    if (isPoppingRef.current) {
      return;
    }

    const interactive =
      interactiveRef.current;

    if (interactive) {
      interactive.style.transition =
        [
          "transform 420ms cubic-bezier(0.22, 1, 0.36, 1)",
          "filter 300ms ease",
        ].join(", ");

      interactive.style.transform =
        [
          "perspective(700px)",
          "translate3d(0, 0, 0)",
          "rotateX(0deg)",
          "rotateY(0deg)",
          "scale(1)",
        ].join(" ");

      interactive.style.filter =
        "drop-shadow(0 8px 16px rgba(60, 45, 30, 0.05))";
    }

    journeyAnimationRef.current?.play();
  };

  const handlePop = () => {
    if (
      isPoppingRef.current ||
      hasCompletedRef.current
    ) {
      return;
    }

    isPoppingRef.current = true;
    hasCompletedRef.current = true;

    journeyAnimationRef.current?.pause();

    const interactive =
      interactiveRef.current;

    if (!interactive) {
      completionCallbackRef.current();
      return;
    }

    /*
     * 1 — object squashes
     * 2 — inflates like a bubble
     * 3 — snaps/collapses
     */
    const popAnimation =
      interactive.animate(
        [
          {
            offset: 0,
            transform:
              "perspective(700px) scale(1.04)",
            opacity: 1,
          },

          {
            offset: 0.16,
            transform:
              "perspective(700px) scale(0.88)",
            opacity: 1,
          },

          {
            offset: 0.42,
            transform:
              "perspective(700px) scale(1.28)",
            opacity: 1,
          },

          {
            offset: 0.58,
            transform:
              "perspective(700px) scale(1.38)",
            opacity: 0.96,
          },

          {
            offset: 0.7,
            transform:
              "perspective(700px) scale(1.5)",
            opacity: 0.35,
          },

          {
            offset: 1,
            transform:
              "perspective(700px) scale(0.05)",
            opacity: 0,
          },
        ],
        {
          duration: 520,
          easing:
            "cubic-bezier(0.16, 1, 0.3, 1)",
          fill: "forwards",
        },
      );

    /*
     * Main bubble shockwave.
     */
    burstRingRef.current?.animate(
      [
        {
          transform: "scale(0.15)",
          opacity: 0,
          borderWidth: "3px",
        },

        {
          transform: "scale(0.45)",
          opacity: 0.75,
          borderWidth: "3px",
        },

        {
          transform: "scale(1.15)",
          opacity: 0.42,
          borderWidth: "2px",
        },

        {
          transform: "scale(1.9)",
          opacity: 0,
          borderWidth: "1px",
        },
      ],
      {
        duration: 540,
        easing: "ease-out",
        fill: "forwards",
      },
    );

    /*
     * Small paper/bubble fragments fire outward.
     */
    const particleContainer =
      particleContainerRef.current;

    if (particleContainer) {
      const particles =
        particleContainer.querySelectorAll(
          "[data-pop-particle]",
        );

      particles.forEach(
        (particle, index) => {
          const element =
            particle as HTMLElement;

          const angle =
            (Math.PI * 2 * index) /
              particles.length +
            Math.random() * 0.3;

          const distance =
            45 + Math.random() * 45;

          const x =
            Math.cos(angle) * distance;

          const y =
            Math.sin(angle) * distance;

          element.animate(
            [
              {
                transform:
                  "translate(-50%, -50%) scale(0.4)",
                opacity: 0,
              },

              {
                offset: 0.15,
                transform:
                  "translate(-50%, -50%) scale(1)",
                opacity: 0.9,
              },

              {
                transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px)) scale(0)`,
                opacity: 0,
              },
            ],
            {
              duration:
                430 +
                Math.random() * 180,

              delay:
                180 +
                Math.random() * 70,

              easing:
                "cubic-bezier(0.22, 1, 0.36, 1)",

              fill: "forwards",
            },
          );
        },
      );
    }

    popAnimation.finished
      .then(() => {
        /*
         * Small pause lets the burst fragments
         * finish before replacement enters.
         */
        window.setTimeout(() => {
          completionCallbackRef.current();
        }, 120);
      })
      .catch(() => {
        completionCallbackRef.current();
      });
  };

  return (
    <div
      ref={stickerRef}
      className={[
        "pointer-events-auto",
        "absolute",
        "aspect-square",
        "select-none",
        "opacity-0",
        "will-change-transform",
        "cursor-pointer",
        "touch-manipulation",
        DEPTH_SIZE_CLASS[depth],
      ].join(" ")}
      style={{
        left: `${startX}%`,
        top: `${startY}%`,

        zIndex:
          depth === "near"
            ? 3
            : depth === "mid"
              ? 2
              : 1,
      }}
      onPointerEnter={
        handlePointerEnter
      }
      onPointerMove={
        handlePointerMove
      }
      onPointerLeave={
        handlePointerLeave
      }
      onClick={handlePop}
      aria-hidden={
        sticker.accessibility.decorative
      }
    >
      <div
        ref={interactiveRef}
        className="relative h-full w-full will-change-transform"
        style={{
          transform:
            "perspective(700px) translate3d(0,0,0) scale(1)",

          transformStyle: "preserve-3d",

          filter:
            "drop-shadow(0 8px 16px rgba(60,45,30,0.05))",
        }}
      >
        <Image
          src={sticker.assetPath}
          alt={
            sticker.accessibility.decorative
              ? ""
              : sticker.accessibility.alt
          }
          fill
          sizes="(max-width: 640px) 130px, (max-width: 1024px) 190px, 260px"
          draggable={false}
          className="pointer-events-none object-contain"
        />
      </div>

      {/* Bubble shockwave */}
      <div
        ref={burstRingRef}
        className="pointer-events-none absolute inset-[12%] rounded-full border-2 border-[#caa77b] opacity-0"
      />

      {/* Burst particles */}
      <div
        ref={particleContainerRef}
        className="pointer-events-none absolute inset-0"
      >
        {PARTICLES.map((particle) => (
          <span
            key={particle}
            data-pop-particle
            className={[
              "absolute",
              "left-1/2",
              "top-1/2",
              "h-2",
              "w-2",
              "rounded-full",
              "bg-[#d8b98e]",
              "opacity-0",
            ].join(" ")}
          />
        ))}
      </div>
    </div>
  );
}