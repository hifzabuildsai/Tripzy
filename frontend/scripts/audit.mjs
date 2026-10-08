import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";

const EXCEPTION = {
  url: "https://github.com/advisories/GHSA-vfj7-8cjw-p6xm",
  expires: "2026-11-08",
};

export function auditFindings(report, lock, today = new Date().toISOString().slice(0, 10)) {
  if (report.error || !report.vulnerabilities || !report.metadata) {
    throw new Error("npm audit returned an invalid report");
  }
  const vulnerabilities = report.vulnerabilities;
  function excepted(name, seen = new Set()) {
    const item = vulnerabilities[name];
    if (!item || seen.has(name) || today >= EXCEPTION.expires) return false;
    if (!item.nodes?.length || !item.nodes.every((node) => lock.packages[node]?.dev === true)) return false;
    const visited = new Set(seen).add(name);
    return item.via?.length > 0 && item.via.every((via) =>
      typeof via === "string" ? excepted(via, visited) : via.url === EXCEPTION.url
    );
  }
  const blocked = [], accepted = [];
  for (const [name, item] of Object.entries(vulnerabilities)) {
    if (!["high", "critical"].includes(item.severity)) continue;
    (excepted(name) ? accepted : blocked).push(name);
  }
  return { blocked, accepted };
}

function main() {
  if (!process.env.npm_execpath) throw new Error("Run via npm run audit");
  const audit = spawnSync(process.execPath, [process.env.npm_execpath, "audit", "--json"], {
    encoding: "utf8", maxBuffer: 8 * 1024 * 1024,
  });
  if (audit.error || ![0, 1].includes(audit.status)) {
    throw new Error("npm audit could not complete");
  }
  const report = JSON.parse(audit.stdout);
  const lock = JSON.parse(readFileSync(new URL("../package-lock.json", import.meta.url), "utf8"));
  const { blocked, accepted } = auditFindings(report, lock);
  console.log(`Frontend audit: ${blocked.length} blocking high/critical findings.`);
  if (accepted.length) {
    console.log(`Reviewed dev-only exception GHSA-vfj7-8cjw-p6xm, expires ${EXCEPTION.expires}: ${accepted.join(", ")}`);
  }
  if (blocked.length) {
    console.error(`Blocked dependencies: ${blocked.join(", ")}`);
    process.exitCode = 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try { main(); } catch (error) {
    console.error(`Frontend audit failed: ${error.message}`);
    process.exitCode = 1;
  }
}
