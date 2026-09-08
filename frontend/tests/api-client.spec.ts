import { expect, test } from "@playwright/test";
import { apiRequest } from "../src/lib/api";

test("API client converts non-JSON error responses into a controlled ApiError", async () => {
  const fetchImpl = globalThis.fetch;
  globalThis.fetch = async () => new Response("Internal Server Error", { status: 400, headers: { "content-type": "text/plain" } });
  await expect(apiRequest("/controlled-error", { auth: false })).rejects.toMatchObject({ message: "The service returned an unexpected response. Please try again.", status: 400 });
  globalThis.fetch = fetchImpl;
});
