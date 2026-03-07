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
  // Redirect deleted admin pages to their new hub destinations
  async redirects() {
    return [
      { source: '/admin/audit', destination: '/compliance?tab=audit', permanent: true },
      { source: '/admin/compliance', destination: '/compliance', permanent: true },
      { source: '/admin/procedures', destination: '/procedures', permanent: true },
      { source: '/admin/faculty-call', destination: '/call-hub', permanent: true },
      { source: '/admin/import', destination: '/hub/import-export', permanent: true },
      { source: '/admin/game-theory', destination: '/analytics?tab=game-theory', permanent: true },
      { source: '/heatmap', destination: '/ops?tab=demand', permanent: true },
      { source: '/conflicts', destination: '/ops?tab=conflicts', permanent: true },
      { source: '/daily-manifest', destination: '/ops?tab=manifest', permanent: true },
      { source: '/call-roster', destination: '/call-hub', permanent: true },
      { source: '/proxy-coverage', destination: '/ops?tab=coverage', permanent: true },
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
