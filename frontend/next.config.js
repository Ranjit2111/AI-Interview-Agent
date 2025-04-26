/** @type {import('next').NextConfig} */
module.exports = {
    reactStrictMode: true,
    env: {
      NEXT_PUBLIC_BACKEND_URL: "http://localhost:8000"
    },
    webpack: (config) => {
      return config;
    },
    // Ensure CSS modules work properly
    images: {
      domains: ['localhost'],
    },
  };
  