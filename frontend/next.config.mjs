import path from 'path';
import { fileURLToPath } from 'url';

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  skipTrailingSlashRedirect: true,
  experimental: { cpus: 1 },
  async rewrites() {
    const api = process.env.API_INTERNAL_URL || 'http://127.0.0.1:8000';
    return [
      { source: '/api/get_current_season', destination: `${api}/api/get_current_season` },
      { source: '/api/:path*', destination: `${api}/api/:path*/` },
    ];
  },
  outputFileTracingRoot: path.dirname(fileURLToPath(import.meta.url)),
  async redirects()
  {
    return [
      {
        source: '/',
        destination: '/home',
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
