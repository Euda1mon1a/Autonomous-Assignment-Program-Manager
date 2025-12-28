/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true, // Re-enabled - fix render loop root cause instead of hiding
  poweredByHeader: false,
  compress: true,
  images: {
    unoptimized: true, // No external images
  },
}

module.exports = nextConfig
