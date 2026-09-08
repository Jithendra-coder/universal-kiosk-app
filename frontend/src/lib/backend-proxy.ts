const DEFAULT_BACKEND_ORIGIN = "http://127.0.0.1:8000";
const BACKEND_PROXY_TIMEOUT_MS = 14_000;
let backendFailureLogged = false;
const REDACTED = "[REDACTED]";
const SENSITIVE_QUERY_PARAMS = new Set([
  "payment_token",
  "token",
  "devicetoken",
  "device_token",
  "access_token",
  "authorization",
  "session",
  "code",
  "pin",
  "provider_reference",
  "polling_secret",
]);

type ProxyOptions = {
  prefix: "/api" | "/uploads" | "";
  timeoutMs?: number;
};

class BackendOriginConfigurationError extends Error {}

export function backendOrigin() {
  const explicitOrigin = process.env.BACKEND_API_ORIGIN?.trim();
  if (explicitOrigin) return validateBackendOrigin(explicitOrigin);

  const publicApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (publicApiUrl?.startsWith("http://") || publicApiUrl?.startsWith("https://")) {
    return validateBackendOrigin(publicApiUrl.replace(/\/api\/?$/, ""));
  }

  return DEFAULT_BACKEND_ORIGIN;
}

export function validateBackendOrigin(value: string) {
  try {
    const origin = new URL(value);
    if (
      !["http:", "https:"].includes(origin.protocol) ||
      !origin.hostname ||
      origin.username ||
      origin.password ||
      origin.search ||
      origin.hash ||
      (origin.pathname && origin.pathname !== "/")
    ) {
      throw new Error("invalid origin");
    }
    return origin.origin;
  } catch {
    throw new BackendOriginConfigurationError("BACKEND_API_ORIGIN must be an http(s) origin without credentials, path, query, or fragment.");
  }
}

export async function proxyToBackend(
  request: Request,
  pathParts: string[],
  { prefix, timeoutMs = BACKEND_PROXY_TIMEOUT_MS }: ProxyOptions
) {
  try {
    const incomingUrl = new URL(request.url);
    const targetPath = [prefix, pathParts.map(encodeURIComponent).join("/")]
      .filter(Boolean)
      .join("/")
      .replace(/\/+/g, "/");
    const targetUrl = new URL(`${targetPath}${incomingUrl.search}`, backendOrigin());
    const method = request.method.toUpperCase();
    const headers = proxyRequestHeaders(request.headers);
    const body = method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer();
    const timeoutSignal = AbortSignal.timeout(timeoutMs);
    const response = await fetch(targetUrl, {
      method,
      headers,
      body,
      cache: "no-store",
      signal: AbortSignal.any([request.signal, timeoutSignal]),
    });
    backendFailureLogged = false;
    const responseHeaders = proxyResponseHeaders(response.headers);
    if (method === "HEAD" || response.status === 204 || response.status === 205 || response.status === 304) {
      return new Response(null, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
      });
    }
    let responseBody: ArrayBuffer;
    try {
      responseBody = await response.arrayBuffer();
    } catch (error) {
      console.error("Backend proxy returned an incomplete response", sanitizeBackendProxyUrl(targetUrl), safeProxyError(error));
      return Response.json(
        {
          error: { code: "BAD_GATEWAY", message: "The application service returned an invalid response. Please try again." },
          detail: "The application service returned an invalid response. Please try again.",
        },
        { status: 502 }
      );
    }
    return new Response(responseBody, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    if (error instanceof BackendOriginConfigurationError) {
      console.error("Backend proxy configuration error", safeProxyError(error));
      return Response.json(
        {
          error: { code: "PROXY_CONFIGURATION_ERROR", message: "The application service is unavailable. Please contact support." },
          detail: "The application service is unavailable. Please contact support.",
        },
        { status: 500 }
      );
    }
    const timeoutSignal = error instanceof DOMException && error.name === "TimeoutError";
    const timedOut = timeoutSignal && !request.signal.aborted;
    if (!backendFailureLogged) {
      backendFailureLogged = true;
      console.error(timedOut ? "Backend proxy timed out" : "Backend proxy unavailable", safeProxyError(error));
    }
    return Response.json(
      timedOut
        ? {
            error: { code: "GATEWAY_TIMEOUT", message: "The application service did not respond in time. Please try again." },
            detail: "The application service did not respond in time. Please try again.",
          }
        : {
            error: { code: "SERVICE_UNAVAILABLE", message: "The application service is temporarily unavailable. Please try again shortly." },
            detail: "The application service is temporarily unavailable. Please try again shortly.",
          },
      { status: timedOut ? 504 : 503 }
    );
  }
}

export function sanitizeBackendProxyUrl(value: URL | string) {
  const url = value instanceof URL ? new URL(value.toString()) : new URL(value);
  for (const key of Array.from(url.searchParams.keys())) {
    if (SENSITIVE_QUERY_PARAMS.has(key.toLowerCase())) {
      url.searchParams.set(key, REDACTED);
    }
  }

  const parts = url.pathname.split("/");
  for (let index = 0; index < parts.length; index += 1) {
    const segment = parts[index];
    const previous = parts[index - 1];
    const twoBack = parts[index - 2];
    if (
      segment &&
      previous === "live" &&
      ["kiosk", "counter", "kitchen", "devices"].includes(twoBack || "")
    ) {
      parts[index] = REDACTED;
    }
    if (segment && previous === "pairing" && twoBack === "devices") {
      parts[index] = REDACTED;
    }
  }
  url.pathname = parts.join("/");
  return `${url.origin}${url.pathname}${url.search}`.replace(/%5BREDACTED%5D/gi, REDACTED);
}

function safeProxyError(error: unknown) {
  if (error instanceof Error) {
    return { name: error.name, message: error.message };
  }
  return { name: "UnknownError" };
}

function proxyRequestHeaders(source: Headers) {
  const headers = new Headers(source);
  [
    "host",
    "connection",
    "content-length",
    "accept-encoding",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "expect",
  ].forEach((name) => headers.delete(name));
  return headers;
}

function proxyResponseHeaders(source: Headers) {
  const headers = new Headers();
  ["content-type", "cache-control", "etag", "last-modified"].forEach((name) => {
    const value = source.get(name);
    if (value) headers.set(name, value);
  });
  const setCookies =
    typeof (source as Headers & { getSetCookie?: () => string[] }).getSetCookie === "function"
      ? (source as Headers & { getSetCookie: () => string[] }).getSetCookie()
      : [];
  if (setCookies.length) {
    setCookies.forEach((value) => headers.append("set-cookie", value));
  } else {
    const setCookie = source.get("set-cookie");
    if (setCookie) headers.append("set-cookie", setCookie);
  }
  return headers;
}
