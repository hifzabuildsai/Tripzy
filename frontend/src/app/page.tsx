import StickerWorld from "@/components/stickers/StickerWorld";

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-[#faf8f4]">
      <StickerWorld />

      <section className="pointer-events-none relative z-10 flex min-h-screen items-center justify-center px-6">
        <div className="pointer-events-auto max-w-xl text-center">
          <p className="mb-3 text-sm uppercase tracking-[0.22em] text-neutral-500">
            Tripzy
          </p>

          <h1 className="text-4xl font-semibold tracking-tight text-neutral-900 sm:text-6xl">
            Where do you want
            <br />
            to go?
          </h1>

          <p className="mx-auto mt-5 max-w-md text-base leading-7 text-neutral-600">
            Tell me what kind of trip you&apos;re dreaming about.
          </p>
        </div>
      </section>
    </main>
  );
}