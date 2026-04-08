/** @type {import('next').NextConfig} */
const isStaticExport = process.env.NEXT_PUBLIC_STATIC_MODE === "true";
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";

const nextConfig = {
  basePath: basePath || undefined,
  typedRoutes: false,
  images: { unoptimized: true },
  ...(isStaticExport
    ? { output: "export" }
    : {
        async rewrites() {
          const backendUrl = (process.env.BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
          return [
            { source: "/api/:path*", destination: `${backendUrl}/api/:path*` },
          ];
        },
      }),
};

export default nextConfig;
