/** @type {import('next').NextConfig} */
module.exports = {
    reactStrictMode: true,
    env: {
      NEXT_PUBLIC_BACKEND_URL: "https://ranjit21-ai-interview-coaching-agent.hf.space"
    },
    webpack: (config) => {
      return config;
    },
    // Ensure CSS modules work properly
    images: {
      domains: ['localhost'],
    },
  };
  