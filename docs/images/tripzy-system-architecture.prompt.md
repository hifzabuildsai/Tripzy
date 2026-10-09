# Architecture image generation record

Tool: built-in image generation/editing. Edit target: `tripzy-system-architecture.png`. Reviewed against accepted main `cece9b10a2db82d471f4c055ddbb883482a44d31` on October 9, 2026.

## Design specification

Landscape engineering infographic for a GitHub README; preserve the existing cream, forest-green and warm-tan palette, rounded cards and restrained travel accents. Show the Vercel frontend, FastAPI on a single Railway Docker replica, public-demo limits, ConversationService, TripManager, research specialists, Gemini via OpenAI Agents SDK, Tavily, itinerary synthesis with deterministic validation, the API save-after-success boundary and TripRepository/Supabase PostgreSQL JSONB. Include saved-trip restoration and the budget-only revision example: rebuild hotels/itinerary, preserve destination/flights/activities. Footer: research candidates, not bookings or guaranteed availability. Logical responsibilities do not imply parallel execution.

## Provider refinement prompt

Make two precise accuracy corrections to this architecture diagram, preserve every other layout and text element. In Gemini provider card change subtitle 'OpenAI Agents SDK' to 'via OpenAI Agents SDK' and replace body with 'Intent interpretation, research and itinerary synthesis.' Add clean thin dashed dependency connections from the Research specialists card and from the Itinerary synthesis card to the Gemini card, routed through the open white gutter on the right of the central backend workflow without crossing text. These are LLM dependencies, not an execution order. Keep the existing solid intent interpretation arrow and the Tavily search arrow. Provider cards represent external services. Ensure all card text stays readable, correct and unclipped. Do not introduce bookings or any new functionality.

Review caught an incorrect itinerary-to-Tavily arrow in the refinement output. That variant was rejected; the following final correction removed it. Gemini's synthesis responsibility remains stated in its card and in the accessible Mermaid/text version.

## Final edit prompt (verbatim)

Exactly one change: REMOVE the bottom dashed arrow that leaves the right edge of 'Itinerary synthesis + deterministic validation', travels right then upwards, and enters the Tavily card. Delete that entire dashed arrow. Do NOT add or reroute any replacement arrow. Leave the dashed arrow from Research specialists to Gemini and the solid double-ended Research specialists↔Tavily arrow unchanged. The itinerary card must have NO connection to Tavily. Keep absolutely all text, colors, cards, geometry and every other connection unchanged.
