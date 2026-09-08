import { proxyToBackend } from "@/lib/backend-proxy";

type Context = { params: Promise<{ path?: string[] }> };
const handle = async (request: Request, context: Context) =>
  proxyToBackend(request, (await context.params).path ?? [], { prefix: "/api" });

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
export const OPTIONS = handle;
