import type { NextConfig } from "next";

const rawBackendUrl =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.BACKEND_URL ||
  "http://127.0.0.1:8000";

const backendBase =
  rawBackendUrl.startsWith("http://") || rawBackendUrl.startsWith("https://")
    ? rawBackendUrl
    : `https://${rawBackendUrl}`;

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendBase.replace(/\/+$/, "")}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;

