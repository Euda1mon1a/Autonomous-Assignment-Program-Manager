/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true, // Re-enabled - fix render loop root cause instead of hiding
  poweredByHeader: false,
  compress: true,
  // Proxy API requests to backend for same-origin cookie handling
  // Docker: uses 'backend' hostname (service name on Docker network)
  // Local: falls back to localhost:8000
  async rewrites() {
    // BACKEND_URL can be set at build time (via ARG in Dockerfile) or runtime
    // Defaults to localhost for local development outside Docker
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    console.log(`[next.config] Rewrites using backend: ${backendUrl}`)
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ]
  },
  images: {
    unoptimized: true, // No external images
  },
  eslint: {
    ignoreDuringBuilds: false,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
}

module.exports = nextConfig
