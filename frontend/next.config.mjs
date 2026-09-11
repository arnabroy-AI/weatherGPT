/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone output for the compose runner stage (D-02): emits
  // .next/standalone/server.js plus static assets. No other behavior changed.
  output: "standalone",
};

export default nextConfig;
