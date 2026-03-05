/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Static export for Firebase Hosting; use NEXT_OUTPUT=standalone for Cloud Run Docker
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : "export",
  // In production, use NEXT_PUBLIC_API_URL (e.g. your Cloud Run URL). Dev uses rewrites.
  async rewrites() {
    if (process.env.NEXT_PUBLIC_API_URL) return [];
    return [
      { source: "/api/:path*", destination: "http://localhost:8000/api/:path*" },
    ];
  },
};

module.exports = nextConfig;
