import { expect, test } from "@playwright/test";
import { backendOrigin, proxyToBackend } from "../src/lib/backend-proxy";

test("proxy uses the configured canonical backend origin", () => {
  const originalOrigin = process.env.BACKEND_API_ORIGIN;
  process.env.BACKEND_API_ORIGIN = "http://127.0.0.1:8000/";
  try {
    expect(backendOrigin()).toBe("http://127.0.0.1:8000");
  } finally {
    if (originalOrigin === undefined) delete process.env.BACKEND_API_ORIGIN;
    else process.env.BACKEND_API_ORIGIN = originalOrigin;
  }
});

test("proxy preserves cookies and upstream responses and returns one structured 503 on downtime", async () => {
  const originalFetch = globalThis.fetch;
  const originalError = console.error;
  const logged: unknown[][] = [];
  const calls: Array<RequestInit | undefined> = [];
  console.error = (...args: unknown[]) => logged.push(args);

  try {
    globalThis.fetch = async (_request, init) => {
      calls.push(init);
      const headers = Object.assign(new Headers({ "content-type": "application/json" }), {
        getSetCookie: () => ["menutap_admin_session=session; HttpOnly; Path=/"],
      });
      return {
        status: 201,
        statusText: "Created",
        headers,
        arrayBuffer: async () => new TextEncoder().encode('{"ok":true}').buffer,
      } as Response;
    };
    const success = await proxyToBackend(new Request("http://localhost/api/auth/login", { headers: { Cookie: "menutap_admin_session=session" } }), ["auth", "login"], { prefix: "/api" });
    expect(success.status).toBe(201);
    expect(await success.json()).toEqual({ ok: true });
    expect(success.headers.get("set-cookie")).toContain("menutap_admin_session");
    expect(new Headers(calls[0]?.headers).get("cookie")).toBe("menutap_admin_session=session");

    globalThis.fetch = async () => new Response("Internal Server Error", { status: 500, headers: { "content-type": "text/plain" } });
    const plainText = await proxyToBackend(new Request("http://localhost/api/health"), ["health"], { prefix: "/api" });
    expect(plainText.status).toBe(500);
    expect(await plainText.text()).toBe("Internal Server Error");

    globalThis.fetch = async () => new Response(null, { status: 204 });
    const empty = await proxyToBackend(new Request("http://localhost/api/health"), ["health"], { prefix: "/api" });
    expect(empty.status).toBe(204);
    expect(await empty.text()).toBe("");

    globalThis.fetch = async () => { throw new TypeError("network unavailable"); };
    const first = await proxyToBackend(new Request("http://localhost/api/health"), ["health"], { prefix: "/api" });
    const second = await proxyToBackend(new Request("http://localhost/api/health"), ["health"], { prefix: "/api" });
    expect(first.status).toBe(503);
    expect(await first.json()).toMatchObject({ error: { code: "SERVICE_UNAVAILABLE" } });
    expect(second.status).toBe(503);
    expect(logged).toHaveLength(1);

    globalThis.fetch = async (_request, init) =>
      new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => reject(init.signal?.reason), { once: true });
      });
    const timeout = await proxyToBackend(new Request("http://localhost/api/health"), ["health"], { prefix: "/api", timeoutMs: 5 });
    expect(timeout.status).toBe(504);
    expect(await timeout.json()).toMatchObject({ error: { code: "GATEWAY_TIMEOUT" } });

    globalThis.fetch = async () =>
      ({
        status: 200,
        statusText: "OK",
        headers: new Headers({ "content-type": "application/json" }),
        arrayBuffer: async () => {
          throw new Error("ResponseAborted");
        },
      }) as unknown as Response;
    const incomplete = await proxyToBackend(new Request("http://localhost/api/onboarding/status"), ["onboarding", "status"], { prefix: "/api" });
    expect(incomplete.status).toBe(502);
    expect(await incomplete.json()).toMatchObject({ error: { code: "BAD_GATEWAY" } });
  } finally {
    globalThis.fetch = originalFetch;
    console.error = originalError;
  }
});
