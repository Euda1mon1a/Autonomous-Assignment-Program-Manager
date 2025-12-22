/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: false, // Disabled temporarily to debug render loop
  poweredByHeader: false,
  compress: true,
  images: {
    unoptimized: true, // No external images
  },
}

module.exports = nextConfig
