/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // HLS/API는 외부 URL(API_BASE_URL, HLS_BASE_URL)로 접근
  async rewrites() {
    return [];
  },
};

module.exports = nextConfig;
