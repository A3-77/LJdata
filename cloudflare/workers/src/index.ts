import { Hono } from "hono";

type Env = {
  SOURCE_FILES: R2Bucket;
  IMPORT_QUEUE: Queue;
  REGION_CODE: string;
  BACKEND_API_BASE_URL: string;
};

const app = new Hono<{ Bindings: Env }>();

app.get("/health", (c) => c.json({ status: "ok", runtime: "cloudflare-worker" }));

app.get("/api/dashboard/overview", async (c) => {
  const url = new URL("/api/dashboard/overview", c.env.BACKEND_API_BASE_URL);
  url.search = new URL(c.req.url).search;
  const response = await fetch(url);
  return new Response(response.body, response);
});

app.post("/api/import/files", async (c) => {
  const form = await c.req.formData();
  const file = form.get("file");

  if (!(file instanceof File)) {
    return c.json({ error: "file is required" }, 400);
  }

  const periodMonth = String(form.get("period_month") || "");
  if (!periodMonth) {
    return c.json({ error: "period_month is required" }, 400);
  }

  const key = `${c.env.REGION_CODE}/${periodMonth}/${Date.now()}-${file.name}`;
  await c.env.SOURCE_FILES.put(key, file.stream(), {
    httpMetadata: { contentType: file.type || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" },
  });

  const job = {
    key,
    file_name: file.name,
    period_month: periodMonth,
    region_code: c.env.REGION_CODE,
    created_at: new Date().toISOString(),
  };

  await c.env.IMPORT_QUEUE.send(job);

  return c.json({
    status: "queued",
    file_key: key,
  });
});

app.get("/api/import/jobs/:jobId", async (c) => {
  const url = new URL(`/api/import/jobs/${c.req.param("jobId")}`, c.env.BACKEND_API_BASE_URL);
  const response = await fetch(url);
  return new Response(response.body, response);
});

export default app;

