import { Hono } from "hono";

type Env = {
  SOURCE_FILES: R2Bucket;
  IMPORT_QUEUE: Queue<ImportQueueMessage>;
  REGION_CODE: string;
  BACKEND_API_BASE_URL: string;
};

type ImportQueueMessage = {
  key: string;
  file_name: string;
  period_month: string;
  region_code: string;
  template_code: string;
  created_at: string;
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
  const url = new URL(c.req.url);
  const form = await c.req.formData();
  const file = form.get("file");

  if (!isUploadFile(file)) {
    return c.json({ error: "file is required" }, 400);
  }

  const periodMonth = String(form.get("period_month") || url.searchParams.get("period_month") || "");
  if (!periodMonth) {
    return c.json({ error: "period_month is required" }, 400);
  }
  const regionCode = String(form.get("region_code") || url.searchParams.get("region_code") || c.env.REGION_CODE);
  const templateCode = String(
    form.get("template_code") || url.searchParams.get("template_code") || "franchise_contribution_v1",
  );

  const key = `${regionCode}/${periodMonth}/${Date.now()}-${file.name}`;
  await c.env.SOURCE_FILES.put(key, file.stream(), {
    httpMetadata: { contentType: file.type || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" },
  });

  const job = {
    key,
    file_name: file.name,
    period_month: periodMonth,
    region_code: regionCode,
    template_code: templateCode,
    created_at: new Date().toISOString(),
  };

  await c.env.IMPORT_QUEUE.send(job);

  return c.json({
    status: "queued",
    file_key: key,
  });
});

app.get("/api/*", (c) => proxyBackend(c.req.raw, c.env.BACKEND_API_BASE_URL));

async function forwardQueuedImport(job: ImportQueueMessage, env: Env) {
  const source = await env.SOURCE_FILES.get(job.key);
  if (!source) {
    throw new Error(`R2 source file not found: ${job.key}`);
  }

  const form = new FormData();
  const workbook = new Blob([await source.arrayBuffer()], {
    type: source.httpMetadata?.contentType || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  form.append("file", workbook, job.file_name);

  const targetUrl = new URL("/api/import/files", env.BACKEND_API_BASE_URL);
  targetUrl.searchParams.set("region_code", job.region_code);
  targetUrl.searchParams.set("template_code", job.template_code);
  targetUrl.searchParams.set("replace_period", "true");

  const response = await fetch(targetUrl, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Backend import failed: ${response.status} ${detail}`);
  }
}

export default {
  fetch: app.fetch,
  async queue(batch: MessageBatch<ImportQueueMessage>, env: Env): Promise<void> {
    for (const message of batch.messages) {
      try {
        await forwardQueuedImport(message.body, env);
        message.ack();
      } catch (error) {
        console.error(error);
        message.retry();
      }
    }
  },
};
