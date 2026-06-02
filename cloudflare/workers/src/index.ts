import { Hono } from "hono";

type Env = {
  SOURCE_FILES: R2Bucket;
  IMPORT_QUEUE: Queue;
  REGION_CODE: string;
  BACKEND_API_BASE_URL: string;
};

type UploadFile = {
  name: string;
  type?: string;
  stream: () => ReadableStream;
};

const app = new Hono<{ Bindings: Env }>();

function isUploadFile(value: unknown): value is UploadFile {
  return (
    typeof value === "object" &&
    value !== null &&
    "name" in value &&
    typeof value.name === "string" &&
    "stream" in value &&
    typeof value.stream === "function"
  );
}

async function proxyBackend(request: Request, backendBaseUrl: string) {
  const sourceUrl = new URL(request.url);
  const targetUrl = new URL(sourceUrl.pathname, backendBaseUrl);
  targetUrl.search = sourceUrl.search;

  const headers = new Headers(request.headers);
  headers.delete("host");

  const response = await fetch(targetUrl, {
    method: request.method,
    headers,
  });

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
}

app.get("/health", (c) => c.json({ status: "ok", runtime: "cloudflare-worker" }));

app.post("/api/import/files", async (c) => {
  const form = await c.req.formData();
  const file = form.get("file");

  if (!isUploadFile(file)) {
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

app.get("/api/*", (c) => proxyBackend(c.req.raw, c.env.BACKEND_API_BASE_URL));

export default app;
