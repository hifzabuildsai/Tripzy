import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import NewTripLanding from "@/components/tripzy/NewTripLanding";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("landing sticker hit testing", () => {
  it("passes empty-page pointer events through while keeping the composer interactive", () => {
    const html = renderToStaticMarkup(<NewTripLanding />);

    expect(html).toMatch(
      /<section class="[^"]*pointer-events-none[^"]*">/,
    );
    expect(html).toMatch(
      /<div class="pointer-events-auto"><div class="mx-auto w-full max-w-\[760px\]">/,
    );
  });
});
