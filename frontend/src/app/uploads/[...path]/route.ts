import { proxyToBackend } from "@/lib/backend-proxy";

type Context = { params: Promise<{ path?: string[] }> };
const handle = async (request: Request, context: Context) =>
  proxyToBackend(request, (await context.params).path ?? [], { prefix: "/uploads" });

export const GET = handle;
export const HEAD = handle;
