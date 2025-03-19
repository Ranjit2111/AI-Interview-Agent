/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#000000',
          800: '#0A0A0A',
          700: '#121212',
          600: '#1A1A1A',
          500: '#222222',
          400: '#2A2A2A',
          300: '#333333',
          200: '#444444',
          100: '#666666',
        },
        accent: {
          yellow: '#FFCC00',
          green: '#00FF66',
          blue: '#00CCFF',
        },
        shaga: {
          primary: '#FFFFFF',
          secondary: '#CCCCCC',
          muted: '#999999',
        }
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'glow': '0 0 15px rgba(255, 204, 0, 0.5)',
        'subtle': '0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.8s ease-in-out',
        'slide-up': 'slideUp 0.5s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      backgroundImage: {
        'dot-pattern': 'radial-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px)',
      },
    },
  },
  plugins: [],
}; 