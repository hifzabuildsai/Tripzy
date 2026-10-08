import test from "node:test";
import assert from "node:assert/strict";
import { auditFindings } from "./audit.mjs";

const advisory = { url: "https://github.com/advisories/GHSA-vfj7-8cjw-p6xm" };
function fixture() {
  return {
    report: { metadata: {}, vulnerabilities: {
      braces: { severity: "high", via: [advisory], nodes: ["node_modules/braces"] },
      micromatch: { severity: "high", via: ["braces"], nodes: ["node_modules/micromatch"] },
    } },
    lock: { packages: { "node_modules/braces": { dev: true }, "node_modules/micromatch": { dev: true } } },
  };
}

test("accepts only the reviewed dev-only advisory and dependency chain", () => {
  const { report, lock } = fixture();
  assert.deepEqual(auditFindings(report, lock, "2026-10-08"), {
    accepted: ["braces", "micromatch"], blocked: [],
  });
});
test("blocks the advisory if present in runtime dependencies", () => {
  const { report, lock } = fixture();
  lock.packages["node_modules/braces"].dev = false;
  assert.equal(auditFindings(report, lock, "2026-10-08").blocked.length, 2);
});
test("blocks new advisories even in the same package", () => {
  const { report, lock } = fixture();
  report.vulnerabilities.braces.via.push({ url: "https://github.com/advisories/new-advisory" });
  assert.equal(auditFindings(report, lock, "2026-10-08").blocked.length, 2);
});
test("expires instead of silently bypassing future reviews", () => {
  const { report, lock } = fixture();
  assert.equal(auditFindings(report, lock, "2026-11-08").blocked.length, 2);
});
test("rejects malformed or failed audit reports", () => {
  assert.throws(() => auditFindings({ error: {} }, { packages: {} }), /invalid report/);
});
