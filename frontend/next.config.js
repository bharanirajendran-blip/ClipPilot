/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: [
      'localhost',
      'localhost:3000',
      'localhost:8000',
      process.env.NEXT_PUBLIC_SUPABASE_URL?.replace('https://', '')?.split('.')[0] + '.supabase.co',
    ],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.supabase.co',
      },
      {
        protocol: 'https',
        hostname: 'api.example.com',
      },
    ],
  },
  typescript: {
    strictNullChecks: true,
  },
}

module.exports = nextConfig
