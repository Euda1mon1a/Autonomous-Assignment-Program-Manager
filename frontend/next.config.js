/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
<<<<<<< HEAD
  reactStrictMode: false, // Disabled temporarily to debug render loop
=======
  reactStrictMode: true,
>>>>>>> origin/docs/session-14-summary
  poweredByHeader: false,
  compress: true,
  images: {
    unoptimized: true, // No external images
  },
}

module.exports = nextConfig
