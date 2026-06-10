#!/usr/bin/env node
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";

const args = new Map();
for (let index = 2; index < process.argv.length; index += 2) {
  const key = process.argv[index];
  const value = process.argv[index + 1];
  if (!key?.startsWith("--") || value === undefined) {
    throw new Error(`Invalid argument near ${key ?? "(empty)"}`);
  }
  args.set(key.slice(2), value);
}

const apiBase = args.get("api-base") ?? "http://127.0.0.1:8000";
const periodMonth = args.get("period-month") ?? "202604";
const regionCode = args.get("region-code") ?? "LN";
const output = resolve(args.get("output") ?? "frontend/src/snapshotData.ts");
const params = `period_month=${encodeURIComponent(periodMonth)}&region_code=${encodeURIComponent(regionCode)}`;

async function fetchJson(path, fallback = undefined) {
  const response = await fetch(`${apiBase}${path}`);
  if (!response.ok) {
    if (fallback !== undefined) {
      return fallback;
    }
    throw new Error(`${response.status} ${response.statusText}: ${path}`);
  }
  return response.json();
}

async function fetchOptional(path, fallback) {
  try {
    return await fetchJson(path, fallback);
  } catch {
    return fallback;
  }
}

const [overview, topRank, bottomRank, siteRank, heatmap] = await Promise.all([
  fetchJson(`/api/dashboard/overview?${params}`),
  fetchJson(`/api/dashboard/franchises/rank?${params}&metric=total_contribution&direction=desc&limit=30`),
  fetchJson(`/api/dashboard/franchises/rank?${params}&metric=total_contribution&direction=asc&limit=12`),
  fetchJson(`/api/dashboard/sites/rank?${params}&metric=total_contribution&direction=desc&limit=12`),
  fetchJson(`/api/dashboard/contribution-flow/heatmap?${params}&scope_type=region&metric=contribution_total&province_limit=12`),
]);

const importJob = await fetchOptional(`/api/import/jobs/latest?${params}`, null);
const jobId = importJob?.job_id ?? 1;
const [importJobs, importValidation, importErrors] = await Promise.all([
  fetchOptional(`/api/import/jobs?${params}&limit=8`, []),
  fetchOptional(`/api/import/jobs/${jobId}/validation-results`, null),
  fetchOptional(`/api/import/jobs/${jobId}/errors`, null),
]);

const snapshotData = {
  overview,
  topRank,
  bottomRank,
  siteRank,
  heatmap,
  importJob,
  importJobs,
  importValidation,
  importErrors,
};

const body = `import type { DashboardData } from "./types";

export const snapshotData = ${JSON.stringify(snapshotData, null, 2)} satisfies DashboardData;
`;

await mkdir(dirname(output), { recursive: true });
await writeFile(output, body, "utf8");
console.log(`Snapshot data written to ${output}`);
