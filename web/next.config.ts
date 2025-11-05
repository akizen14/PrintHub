import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  webpack: (config) => {
    // Ignore canvas module (used by pdfjs but not needed in browser)
    config.resolve.alias.canvas = false;
    return config;
  },
};

export default nextConfig;
