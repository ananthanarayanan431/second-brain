import type { NextConfig } from "next";

// The FastAPI backend (second_brain/main.py). The browser only ever calls
// /api/*, which Next.js forwards here, so the backend needs no CORS setup.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND_URL}/:path*` }];
  },
};

export default nextConfig;
