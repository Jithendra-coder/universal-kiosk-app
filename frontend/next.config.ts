import type { NextConfig } from "next";
import { validateBackendOrigin } from "./src/lib/backend-proxy";

if (process.env.BACKEND_API_ORIGIN) {
  validateBackendOrigin(process.env.BACKEND_API_ORIGIN);
}

const nextConfig: NextConfig = {
  allowedDevOrigins: ["localhost", "127.0.0.1"],
};

export default nextConfig;
